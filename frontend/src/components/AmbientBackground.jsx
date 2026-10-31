import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from "motion/react";
import { useEffect } from "react";

/**
 * One ambient effect: a fine grid, a slow drifting glow and a spotlight that
 * follows the cursor. All of it is tinted by the current verdict colour
 * (--tint) so the whole scene shifts hue when a result arrives.
 */
export default function AmbientBackground() {
  const reduce = useReducedMotion();
  const x = useMotionValue(0.5);
  const y = useMotionValue(0.3);
  const sx = useSpring(x, { stiffness: 60, damping: 20, mass: 0.6 });
  const sy = useSpring(y, { stiffness: 60, damping: 20, mass: 0.6 });
  const left = useTransform(sx, (v) => `${v * 100}%`);
  const top = useTransform(sy, (v) => `${v * 100}%`);

  useEffect(() => {
    if (reduce) return undefined;
    const move = (e) => {
      x.set(e.clientX / window.innerWidth);
      y.set(e.clientY / window.innerHeight);
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, [reduce, x, y]);

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-ink">
      <div className="grid-bg absolute inset-0" />
      <motion.div
        className="absolute h-[70vmax] w-[70vmax] -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{
          left,
          top,
          background: "radial-gradient(closest-side, rgba(var(--tint), 0.16), transparent 70%)",
          transition: "background 1.2s var(--ease-out-expo)",
        }}
      />
      {!reduce && (
        <motion.div
          className="absolute -right-[20vmax] -top-[25vmax] h-[60vmax] w-[60vmax] rounded-full opacity-60"
          style={{ background: "radial-gradient(closest-side, rgba(var(--tint), 0.10), transparent 70%)" }}
          animate={{ x: [0, -60, 20, 0], y: [0, 40, -20, 0] }}
          transition={{ duration: 28, repeat: Infinity, ease: "easeInOut" }}
        />
      )}
      <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-ink to-transparent" />
    </div>
  );
}
