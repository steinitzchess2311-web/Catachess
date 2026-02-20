import React from 'react';

interface Props {
  children: React.ReactNode;
  /** Custom fallback UI. If omitted a default card is shown. */
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * StudyErrorBoundary — catches any render-phase exception in the study tree
 * and shows a recoverable error card instead of a white screen.
 *
 * Usage:
 *   <StudyErrorBoundary>
 *     <StudyProvider>...</StudyProvider>
 *   </StudyErrorBoundary>
 */
export class StudyErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[StudyErrorBoundary]', error.message, info.componentStack);
  }

  private reset = () => this.setState({ hasError: false, error: null });

  render() {
    if (!this.state.hasError) return this.props.children;
    if (this.props.fallback) return this.props.fallback;

    return (
      <div className="patch-error-boundary">
        <h3>Something went wrong</h3>
        <p className="patch-error-message">{this.state.error?.message ?? 'Unknown error'}</p>
        <button type="button" className="patch-modal-button primary" onClick={this.reset}>
          Try again
        </button>
      </div>
    );
  }
}
