import Sidebar from './components/Sidebar/SpaceList'
import MainArea from './components/MainArea/CollectionGrid'
import Header from './components/Header'

function App() {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Open Tabs</h1>
        </div>
        <Sidebar />
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <MainArea />
        </main>
      </div>
    </div>
  )
}

export default App
