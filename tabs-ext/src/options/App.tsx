function App() {
  return (
    <div className="max-w-2xl mx-auto p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="space-y-6">
        {/* Account Section */}
        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Account</h2>
          <p className="text-gray-600">Account settings will be available here.</p>
        </section>

        {/* Sync Section */}
        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sync</h2>
          <p className="text-gray-600">Sync settings will be available here.</p>
        </section>

        {/* Data Section */}
        <section className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Data</h2>
          <div className="space-y-3">
            <button className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700">
              Export Data
            </button>
            <button className="px-4 py-2 ml-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300">
              Import Data
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}

export default App
