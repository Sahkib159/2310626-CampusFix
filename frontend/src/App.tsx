
import { BrowserRouter, Route, Routes } from "react-router"

import HomePage from "./pages/HomePage"
import RequestDetailsPage from "./pages/RequestDetailsPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/requests/:id" element={<RequestDetailsPage />} />
      </Routes>
    </BrowserRouter>
  )
}
