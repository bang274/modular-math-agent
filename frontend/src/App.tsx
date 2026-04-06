import { useEffect } from 'react'
import { Layout } from './components/layout/Layout'
import { Sidebar } from './components/chat/Sidebar'
import { ChatWindow } from './components/chat/ChatWindow'
import { useChatStore } from './store/chatStore'
import './App.css'

function App() {

  useEffect(() => {
    if (!useChatStore.getState().activeId) {
      useChatStore.getState().newConversation()
    }
  }, [])

  return (
    <Layout>
      <div className="app-body">
        <Sidebar />
        <ChatWindow />
      </div>
    </Layout>
  )
}

export default App

