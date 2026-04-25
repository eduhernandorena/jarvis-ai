import { useState, useCallback, useRef } from 'react';

// Declarations for Web Speech API to avoid TS errors
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export function useSpeech() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef<any>(null);
  const micStreamRef = useRef<MediaStream | null>(null);

  const startListening = useCallback(() => {
    console.log("startListening() chamado");
    if (typeof window === 'undefined') return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Speech API não suportada');
      return;
    }

    // Mata instância anterior
    if (recognitionRef.current) {
      try { recognitionRef.current.abort(); } catch (e) {}
    }
    // Mata stream anterior
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(t => t.stop());
      micStreamRef.current = null;
    }

    // ESTRATÉGIA: Abrir getUserMedia PRIMEIRO e MANTER ABERTO
    // enquanto o SpeechRecognition roda. Isso força o iOS a
    // manter o roteamento de áudio no microfone.
    const launchRecognition = (stream: MediaStream | null) => {
      if (stream) {
        micStreamRef.current = stream;
        console.log("Stream de mic mantido ATIVO durante reconhecimento");
      }

      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = true;
      rec.lang = 'pt-BR';

      rec.onstart = () => console.log("REC: onstart");
      rec.onaudiostart = () => console.log("REC: onaudiostart");
      rec.onsoundstart = () => console.log("REC: onsoundstart");
      rec.onspeechstart = () => console.log("REC: onspeechstart");
      rec.onspeechend = () => console.log("REC: onspeechend");
      rec.onaudioend = () => console.log("REC: onaudioend");

      rec.onresult = (event: any) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          currentTranscript += event.results[i][0].transcript;
        }
        console.log("REC: resultado = " + currentTranscript);
        setTranscript(currentTranscript);
      };

      rec.onend = () => {
        console.log("REC: onend");
        // Libera o stream do microfone quando o reconhecimento terminar
        if (micStreamRef.current) {
          micStreamRef.current.getTracks().forEach(t => t.stop());
          micStreamRef.current = null;
          console.log("Stream de mic liberado");
        }
        setIsListening(false);
      };

      rec.onerror = (event: any) => {
        console.error("REC: erro = " + event.error);
        if (micStreamRef.current) {
          micStreamRef.current.getTracks().forEach(t => t.stop());
          micStreamRef.current = null;
        }
        setIsListening(false);
      };

      recognitionRef.current = rec;
      setTranscript('');

      try {
        rec.start();
        setIsListening(true);
        console.log("REC: start() OK");
      } catch (e) {
        console.error("REC: start() FALHOU", e);
        setIsListening(false);
      }
    };

    // Abre o microfone real via getUserMedia e MANTÉM aberto
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      console.log("Abrindo getUserMedia (manterá aberto)...");
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          console.log("getUserMedia aberto com sucesso");
          // Espera 200ms para o iOS estabilizar o roteamento
          setTimeout(() => launchRecognition(stream), 200);
        })
        .catch(err => {
          console.error("getUserMedia falhou:", err);
          launchRecognition(null);
        });
    } else {
      launchRecognition(null);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(t => t.stop());
      micStreamRef.current = null;
    }
  }, []);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    hasSupport: typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  };
}
