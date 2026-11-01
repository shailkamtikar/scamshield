import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from "motion/react";
import { useEffect } from "react";

/**
 * Quiet atmosphere: one soft light that follows the cursor slowly, a grain layer, and a vignette.
 * The light takes the verdict colour (--tint) once a result is on screen.
 */
export default function AmbientBackground() {
  const reduce = useReducedMotion();
  const x = useMotionValue(0.5);
  const y = useMotionValue(0.25);
  const sx = useSpring(x, { stiffness: 40, damping: 22, mass: 0.8 });
  const sy = useSpring(y, { stiffness: 40, damping: 22, mass: 0.8 });
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
      <motion.div
        className="absolute h-[60vmax] w-[60vmax] -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{ left, top, background: "radial-gradient(closest-side, rgba(var(--tint), 0.075), transparent 70%)" }}
      />
      <div className="noise absolute inset-0" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,transparent_40%,var(--vignette)_100%)]" />
    </div>
  );
}
