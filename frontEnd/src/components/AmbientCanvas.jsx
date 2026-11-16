import { useEffect, useRef } from 'react';

/**
 * AmbientCanvas — Reusable HTML5 Canvas 2D Particle System
 * Spec: Section 4 of ANTIGRAVITY_FRONTEND_INSTRUCTIONS.md
 * 
 * Props:
 * - cursorInfluence (boolean): Boosts particle alpha near mouse position within 160px
 * - crimsonGlow (boolean): Draws a bottom radial crimson glow gradient
 * - loginGradients (boolean): Special corner gradients for Login screen (Screen 1)
 */
export default function AmbientCanvas({
  cursorInfluence = false,
  crimsonGlow = false,
  loginGradients = false,
  className = '',
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    // Mouse tracking for cursorInfluence
    const mouse = { x: -9999, y: -9999 };

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    const handleMouseLeave = () => {
      mouse.x = -9999;
      mouse.y = -9999;
    };

    // Attach mouse listeners to parent element if cursorInfluence enabled
    const parentEl = canvas.parentElement || window;
    if (cursorInfluence && parentEl) {
      parentEl.addEventListener('mousemove', handleMouseMove);
      parentEl.addEventListener('mouseleave', handleMouseLeave);
    }

    const handleResize = () => {
      width = canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
      height = canvas.height = canvas.parentElement?.clientHeight || window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // 65 particles per spec:
    // radius 0.35–1.45px, velocity ±0.22px/frame, base alpha 0.04–0.21, bounce off edges
    const PARTICLE_COUNT = 65;
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() * 0.44 - 0.22),
      vy: (Math.random() * 0.44 - 0.22),
      radius: 0.35 + Math.random() * 1.1,
      baseAlpha: 0.04 + Math.random() * 0.17,
    }));

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // 1. Crimson Glow Prop (Section 4)
      if (crimsonGlow) {
        const glowRadius = height * 0.7;
        const grad = ctx.createRadialGradient(
          width * 0.5,
          height,
          0,
          width * 0.5,
          height,
          glowRadius
        );
        grad.addColorStop(0, 'rgba(254, 239, 184, 0.040)');
        grad.addColorStop(1, 'transparent');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, width, height);
      }

      // 2. Login Screen Corner Gradients (Section 6 Screen 1)
      if (loginGradients) {
        // Bottom-left gradient: brown/chocopie warm glow
        const blGrad = ctx.createRadialGradient(0, height, 0, 0, height, 440);
        blGrad.addColorStop(0, 'rgba(67, 47, 46, 0.50)');
        blGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = blGrad;
        ctx.fillRect(0, 0, width, height);

        // Top-right gradient: blue accent
        const trGrad = ctx.createRadialGradient(width, 0, 0, width, 0, 340);
        trGrad.addColorStop(0, 'rgba(196, 218, 232, 0.05)');
        trGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = trGrad;
        ctx.fillRect(0, 0, width, height);
      }

      // 3. Update & Draw Particles
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        // Bounce off all four edges
        if (p.x <= 0 || p.x >= width) p.vx *= -1;
        if (p.y <= 0 || p.y >= height) p.vy *= -1;

        // Keep within bounds
        if (p.x < 0) p.x = 0;
        if (p.x > width) p.x = width;
        if (p.y < 0) p.y = 0;
        if (p.y > height) p.y = height;

        // Calculate dynamic alpha with cursor influence (within 160px)
        let alpha = p.baseAlpha;
        if (cursorInfluence) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 160) {
            alpha += (1 - dist / 160) * 0.28;
          }
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.min(alpha, 1)})`;
        ctx.fill();
      }

      // 4. Draw Connection Lines (Section 4)
      // Every pair within 112px draws a line at rgba(255,255,255, 0.038*(1-distance/112)), lineWidth 0.5
      ctx.lineWidth = 0.5;
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const p1 = particles[i];
        for (let j = i + 1; j < PARTICLE_COUNT; j++) {
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 112) {
            const lineAlpha = 0.038 * (1 - dist / 112);
            ctx.strokeStyle = `rgba(255, 255, 255, ${lineAlpha})`;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      if (cursorInfluence && parentEl) {
        parentEl.removeEventListener('mousemove', handleMouseMove);
        parentEl.removeEventListener('mouseleave', handleMouseLeave);
      }
    };
  }, [cursorInfluence, crimsonGlow, loginGradients]);

  return (
    <canvas
      ref={canvasRef}
      className={`ambient-canvas ${className}`}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 1,
      }}
    />
  );
}
