import { useRef, useCallback } from 'react';

export function useJarvisAudio() {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const audioQueue = useRef<string[]>([]);
  const isPlaying = useRef<boolean>(false);
  const endOfStream = useRef<boolean>(false);

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
      audioCtxRef.current = new AudioCtx();
    }
    return audioCtxRef.current;
  }, []);

  const playBase64Audio = useCallback(async (base64: string): Promise<void> => {
    return new Promise(async (resolve) => {
      try {
        const ctx = getAudioContext();
        if (!ctx) { resolve(); return; }
        
        if (ctx.state === 'suspended') {
          await ctx.resume();
        }

        const binaryString = atob(base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }

        const audioBuffer = await ctx.decodeAudioData(bytes.buffer.slice(0));
        
        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(ctx.destination);
        
        source.onended = () => {
          currentSourceRef.current = null;
          resolve();
        };
        
        currentSourceRef.current = source;
        source.start(0);
      } catch (e) {
        console.error("Web Audio playback error:", e);
        resolve();
      }
    });
  }, [getAudioContext]);

  const playNextAudio = useCallback(async (onFinish?: () => void) => {
    if (audioQueue.current.length === 0) {
      isPlaying.current = false;
      if (endOfStream.current && onFinish) {
        onFinish();
      }
      return;
    }
    
    isPlaying.current = true;
    const base64 = audioQueue.current.shift();
    if (base64) {
      await playBase64Audio(base64);
      playNextAudio(onFinish);
    }
  }, [playBase64Audio]);

  const stopAllAudio = useCallback(() => {
    if (currentSourceRef.current) {
      try { currentSourceRef.current.stop(); } catch(e) {}
      currentSourceRef.current = null;
    }
    audioQueue.current = [];
    isPlaying.current = false;
    endOfStream.current = false;
  }, []);

  const addToQueue = useCallback((base64: string, onFinish?: () => void) => {
    audioQueue.current.push(base64);
    if (!isPlaying.current) {
      playNextAudio(onFinish);
    }
  }, [playNextAudio]);

  const setEndOfStream = useCallback((value: boolean) => {
    endOfStream.current = value;
  }, []);

  return {
    getAudioContext,
    stopAllAudio,
    addToQueue,
    setEndOfStream,
    isAudioPlaying: isPlaying
  };
}
