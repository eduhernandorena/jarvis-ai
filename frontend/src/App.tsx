import { useState, useEffect } from 'react';
import { JarvisOrb, type OrbState } from './components/JarvisOrb';
import { useSpeech } from './hooks/useSpeech';
import { useJarvisAudio } from './hooks/useJarvisAudio';
import './App.css';

const BACKEND_URL = 'https://jarvis-brazil-mvp.loca.lt';

function App() {
  const [orbState, setOrbState] = useState<OrbState>('idle');
  const [conversation, setConversation] = useState<{role: 'user' | 'jarvis', text: string}[]>([]);
  const [manualText, setManualText] = useState('');
  
  const { isListening, transcript, startListening, stopListening, hasSupport } = useSpeech();
  const { getAudioContext, stopAllAudio, addToQueue, setEndOfStream } = useJarvisAudio();

  // Gerencia transição de estados de voz (Microfone -> Processamento)
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
    setOrbState('processing');
    setConversation(prev => [...prev, { role: 'user', text }]);
    setEndOfStream(false);

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Bypass-Tunnel-Reminder': 'true' },
        body: JSON.stringify({ message: text })
      });

      if (!response.ok || !response.body) throw new Error('Falha na comunicação');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamBuffer = '';
      
      setConversation(prev => [...prev, { role: 'jarvis', text: '' }]);
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
          const data = JSON.parse(line);
          
          setConversation(prev => {
            const newConv = [...prev];
            const lastIdx = newConv.length - 1;
            newConv[lastIdx].text += (newConv[lastIdx].text ? ' ' : '') + data.text;
            return newConv;
          });
          
          if (data.audio) {
            addToQueue(data.audio, () => setOrbState('idle'));
          }
        }
      }
    } catch (error) {
      console.error("Backend error:", error);
      setConversation(prev => [...prev, { role: 'jarvis', text: 'Erro na comunicação.' }]);
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

  const handleOrbClick = () => {
    if (orbState === 'idle') {
      const ctx = getAudioContext();
      if (ctx?.state === 'suspended') ctx.resume();
      startListening();
    } else if (orbState === 'listening') {
      stopListening();
    } else if (orbState === 'speaking') {
      stopAllAudio();
      setOrbState('idle');
    }
  };

  if (!hasSupport) {
    return (
      <div className="unsupported-screen">
        <h1>Navegador não suportado.</h1>
        <p>Use Chrome ou Safari para o Jarvis funcionar.</p>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>J.A.R.V.I.S</h1>
        <p>Sistema Operacional Inteligente</p>
      </header>

      <main className="main-content">
        <JarvisOrb state={orbState} onClick={handleOrbClick} />
        
        <div className="transcript-box">
          {isListening && transcript && <p className="live-transcript">"{transcript}"</p>}
        </div>

        <form className="manual-input-form" onSubmit={handleManualSubmit}>
          <input 
            type="text" placeholder="Comando..." value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            disabled={orbState !== 'idle'}
          />
          <button type="submit" disabled={orbState !== 'idle' || !manualText.trim()}>Enviar</button>
        </form>
      </main>

      <section className="conversation-history">
         {conversation.slice(-2).map((msg, idx) => (
           <div key={idx} className={`message ${msg.role}`}>
              <span className="sender">{msg.role === 'user' ? 'Você' : 'Jarvis'}</span>
              <p>{msg.text}</p>
           </div>
         ))}
      </section>
    </div>
  );
}

export default App;
