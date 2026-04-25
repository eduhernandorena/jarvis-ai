import { motion, type Variants } from 'framer-motion';
import { Mic, Loader2, Volume2 } from 'lucide-react';
import './JarvisOrb.css';

export type OrbState = 'idle' | 'listening' | 'processing' | 'speaking';

interface JarvisOrbProps {
  state: OrbState;
  onClick: () => void;
}

export function JarvisOrb({ state, onClick }: JarvisOrbProps) {
  // Determine pulse animation based on state
  const pulseVariants: Variants = {
    idle: {
      scale: [1, 1.05, 1],
      boxShadow: [
        '0 0 20px rgba(0, 191, 255, 0.4)',
        '0 0 40px rgba(0, 191, 255, 0.6)',
        '0 0 20px rgba(0, 191, 255, 0.4)',
      ],
      transition: { duration: 4, repeat: Infinity, ease: "easeInOut" }
    },
    listening: {
      scale: [1, 1.15, 1],
      boxShadow: [
        '0 0 30px rgba(0, 255, 128, 0.6)',
        '0 0 60px rgba(0, 255, 128, 0.9)',
        '0 0 30px rgba(0, 255, 128, 0.6)',
      ],
      transition: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
    },
    processing: {
      scale: [1, 1.1, 1.05, 1.15, 1],
      boxShadow: [
        '0 0 40px rgba(138, 43, 226, 0.7)',
        '0 0 80px rgba(138, 43, 226, 0.9)',
        '0 0 40px rgba(138, 43, 226, 0.7)',
      ],
      transition: { duration: 1, repeat: Infinity, ease: "linear" }
    },
    speaking: {
      scale: [1, 1.2, 1.05, 1.3, 1],
      boxShadow: [
        '0 0 50px rgba(0, 191, 255, 0.8)',
        '0 0 100px rgba(0, 191, 255, 1)',
        '0 0 50px rgba(0, 191, 255, 0.8)',
      ],
      transition: { duration: 0.5, repeat: Infinity, ease: "circIn" } // Fast erratic pulse for speaking
    }
  };

  const getIcon = () => {
    switch (state) {
      case 'idle': return <Mic className="orb-icon" size={32} />;
      case 'listening': return <Mic className="orb-icon text-green-400" size={32} />;
      case 'processing': return <Loader2 className="orb-icon animate-spin" size={32} />;
      case 'speaking': return <Volume2 className="orb-icon" size={32} />;
    }
  };

  const getStateText = () => {
    switch (state) {
      case 'idle': return 'Aguardando Comando...';
      case 'listening': return 'Ouvindo...';
      case 'processing': return 'Processando...';
      case 'speaking': return 'Falando...';
    }
  };

  return (
    <div className="orb-container">
      <motion.div
        className={`jarvis-orb state-${state}`}
        animate={state}
        variants={pulseVariants}
        onClick={onClick}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="orb-core">
          {getIcon()}
        </div>
      </motion.div>
      <div className="orb-status">
        {getStateText()}
      </div>
    </div>
  );
}
