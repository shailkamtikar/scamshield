import { Component } from "react";

/** Keeps a rendering bug from leaving a blank page. */
export default class ErrorBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="mx-auto max-w-[560px] px-6 py-28">
        <div className="label mb-3 text-danger">Something broke</div>
        <h1 className="display text-[clamp(2.4rem,8vw,4.5rem)]">Please reload.</h1>
        <p className="mt-4 text-muted">This is a problem on our side. Reloading the page usually fixes it.</p>
        <button type="button" onClick={() => window.location.reload()} className="mt-8 border border-[rgb(var(--tint))] px-6 py-3 text-[13px] font-semibold uppercase tracking-[0.12em] tint-text transition-colors hover:bg-[rgb(var(--tint))] hover:text-ink">Reload</button>
      </div>
    );
  }
}
