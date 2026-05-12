import { useEffect, useRef } from 'react';

export default function CursorGlow() {
  const glowRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (glowRef.current) {
        // Center the 600x600 glow div on the cursor
        glowRef.current.style.transform = `translate(${e.clientX - 300}px, ${e.clientY - 300}px)`;
      }
    };
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div
      ref={glowRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '600px',
        height: '600px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(0,212,255,0.12) 0%, transparent 60%)',
        pointerEvents: 'none',
        transform: `translate(-1000px, -1000px)`,
        zIndex: 9998,
        transition: 'transform 0.08s ease-out',
        mixBlendMode: 'screen',
        willChange: 'transform'
      }}
    />
  );
}
