import './App.css'
import { useDb } from './db/index.ts'
import { LoadingScreen } from './components/LoadingScreen.tsx'
import { ErrorScreen } from './components/ErrorScreen.tsx'
import { ReaderPage } from './components/ReaderPage.tsx'

function App() {
  const state = useDb()
  if (state.status === 'loading') return <LoadingScreen />
  if (state.status === 'error') return <ErrorScreen error={state.error} />
  return (
    <div className="app">
      <ReaderPage />
    </div>
  )
}

export default App
