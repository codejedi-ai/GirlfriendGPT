import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { documentTitle, PRODUCT_DESCRIPTION } from './config/brand'
import './index.css'

document.title = documentTitle()
const metaDescription = document.querySelector('meta[name="description"]')
if (metaDescription) metaDescription.setAttribute('content', PRODUCT_DESCRIPTION)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
