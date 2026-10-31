import { Component } from "react";

/** Keeps a rendering bug from leaving people with a blank page. */
export default class ErrorBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="mx-auto max-w-[560px] px-6 py-24 text-center">
        <h1 className="text-[28px]">Something went wrong on this page</h1>
        <p className="mt-3 text-soft">This is a problem on our side. Reloading the page usually fixes it.</p>
        <button type="button" className="btn-primary mt-6" onClick={() => window.location.reload()}>Reload the page</button>
      </div>
    );
  }
}
