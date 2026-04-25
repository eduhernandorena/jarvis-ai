import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { JarvisOrb } from './components/JarvisOrb';
import { useSpeech } from './hooks/useSpeech';
import { useJarvisAudio } from './hooks/useJarvisAudio';

const BACKEND_URL = "http://localhost:8000";

interface Message {
  role: 'user' | 'jarvis';
  text: string;
}

function App() {
  const [conversation, setConversation] = useState<Message[]>([]);
  const [orbState, setOrbState] = useState<'idle' | 'listening' | 'processing' | 'speaking'>('idle');
  const [manualText, setManualText] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [personality, setPersonality] = useState<'jarvis' | 'friday' | 'karen'>('jarvis');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  const { isListening, transcript, startListening, stopListening, hasSupport } = useSpeech();
  const { getAudioContext, stopAllAudio, addToQueue, setEndOfStream } = useJarvisAudio();

  // Atualiza o título e o ícone da aba dinamicamente
  useEffect(() => {
    document.title = `${personality.toUpperCase()} AI | HUD OS`;
    
    // Força a atualização do Favicon
    const link: any = document.querySelector("link[rel~='icon']") || document.createElement('link');
    link.type = 'image/png';
    link.rel = 'icon';
    link.href = '/favicon.png?v=' + new Date().getTime();
    document.getElementsByTagName('head')[0].appendChild(link);
  }, [personality]);


  const handleStopAll = () => {
    abortControllerRef.current?.abort();
    stopAllAudio();
    setOrbState('idle');
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  // Alertas Iniciais (Briefing)
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/alerts`, {
          headers: { 'Bypass-Tunnel-Reminder': 'true' }
        });
        const data = await res.json();
        if (data.alert) {
          setConversation(prev => {
            // Evita duplicar ou substituir o briefing se ele já existir
            if (prev.length === 0) return [{ role: 'jarvis', text: data.alert }];
            return prev;
          });
        }
      } catch (err) {
        console.log("Briefing indisponível.");
      }
    };
    fetchAlerts();
  }, []);

  useEffect(() => {
    if (isListening) {
      setOrbState('listening');
    } else if (orbState === 'listening') {
      if (transcript.trim()) {
        handleProcessTranscript(transcript);
      } else {
        setOrbState('idle');
      }
    }
  }, [isListening, transcript]);

  const handleProcessTranscript = async (text: string) => {
    stopListening();
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();

    setOrbState('processing');
    
    // Adiciona User e placeholder Jarvis ao final do histórico SEM APAGAR O BRIEFING
    setConversation(prev => {
      const news = [...prev, { role: 'user' as const, text }];
      news.push({ role: 'jarvis' as const, text: '' });
      return news;
    });
    setEndOfStream(false);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, personality }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok || !response.body) throw new Error('Falha');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamBuffer = '';
      
      setOrbState('speaking');

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          setEndOfStream(true);
          break;
        }
        
        streamBuffer += decoder.decode(value, { stream: true });
        const lines = streamBuffer.split('\n');
        streamBuffer = lines.pop() || '';
        
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.text) {
              setConversation(prev => {
                const newConv = [...prev];
                // Atualiza APENAS a última mensagem (a do Jarvis atual)
                newConv[newConv.length - 1].text = data.text;
                return newConv;
              });
            }
            if (data.audio) {
              addToQueue(data.audio, () => setOrbState('idle'));
            }
          } catch (e) {}
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return;
      setOrbState('idle');
    }
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (manualText.trim()) {
      handleProcessTranscript(manualText);
      setManualText('');
    }
  };

  if (!hasSupport) return <div className="p-10">Navegador incompatível.</div>;

  return (
    <div className="app-container" data-personality={personality}>
      <header className="app-header">
        <h1>{personality.toUpperCase()} AI</h1>
        <div className="personality-selector">
          {(['jarvis', 'friday', 'karen'] as const).map(p => (
            <button key={p} className={`p-btn ${personality === p ? 'active' : ''}`} onClick={() => setPersonality(p)}>
              {p.toUpperCase()}
            </button>
          ))}
        </div>
      </header>

      <main className="main-content">
        <JarvisOrb state={orbState} onClick={() => {
          if (orbState === 'idle') { getAudioContext(); startListening(); }
          else if (orbState === 'listening') stopListening();
          else if (orbState === 'speaking') handleStopAll();
        }} />
        
        <div className="transcript-box">
          {isListening && transcript && <p className="live-transcript">{transcript}</p>}
          {orbState === 'speaking' && <button className="stop-speech-btn" onClick={handleStopAll}>STOP</button>}
        </div>

        <form className="manual-input-form" onSubmit={handleManualSubmit}>
          <input type="text" placeholder="Aguardando comando..." value={manualText} onChange={(e) => setManualText(e.target.value)} />
          <button type="submit" disabled={orbState === 'processing'}>ENVIAR</button>
        </form>

        <section className="conversation-history">
          {conversation.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <p>{msg.text}</p>
            </div>
          ))}
          <div ref={chatEndRef} />
        </section>
      </main>
    </div>
  );
}

export default App;
