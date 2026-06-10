import * as webllm from '@mlc-ai/web-llm'

const MODEL_ID = 'Llama-3.2-3B-Instruct-q4f16_1-MLC'

type ProgressCallback = (progress: number) => void

const _progressListeners = new Set<ProgressCallback>()
let _enginePromise: Promise<webllm.MLCEngine> | null = null

export function subscribeProgress(cb: ProgressCallback): () => void {
  _progressListeners.add(cb)
  return () => _progressListeners.delete(cb)
}

export function getEngine(): Promise<webllm.MLCEngine> {
  if (!_enginePromise) {
    _enginePromise = webllm.CreateMLCEngine(MODEL_ID, {
      initProgressCallback: (report) => {
        const pct = Math.round((report.progress ?? 0) * 100)
        _progressListeners.forEach(cb => cb(pct))
        if (report.progress >= 1) _progressListeners.clear()
      },
    })
  }
  return _enginePromise
}
