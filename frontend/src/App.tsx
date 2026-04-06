import { Layout } from './components/layout/Layout'
import { UploadZone } from './components/upload/UploadZone'
import { SolveView } from './components/solve/SolveView'
import './App.css'

function App() {
  return (
    <Layout>
      <div className="page-home">
        <div className="hero">
          <h1 className="hero-title">
            <span className="hero-gradient">Math AI Agent</span>
            <br />Pipeline
          </h1>
          <p className="hero-subtitle">
            Upload đề bài toán — nhận lời giải step-by-step với AI Agent thông minh.
            <br />
            Hỗ trợ text, ảnh, hoặc cả hai. Giải song song nhiều bài cùng lúc.
          </p>
        </div>

        <UploadZone />
        <SolveView />
      </div>
    </Layout>
  )
}

export default App
