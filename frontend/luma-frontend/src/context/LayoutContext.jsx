import { createContext, useContext, useEffect, useState } from 'react'
import { TEMPLATES, DEFAULT_TEMPLATE_ID, getTemplateById } from '../templates/registry'

const LayoutContext = createContext(null)

export function LayoutProvider({ children }) {
  const [templateId, setTemplateId] = useState(
    () => localStorage.getItem('luma_template') || DEFAULT_TEMPLATE_ID
  )

  // Mirrors the approach in ThemeContext: the selected template is published to
  // the document as a data attribute so stylesheets can scope overrides under
  // [data-template="soft"] without any page component needing to know about it.
  useEffect(() => {
    const template = getTemplateById(templateId)
    document.documentElement.dataset.template = template.id
    localStorage.setItem('luma_template', template.id)
  }, [templateId])

  const value = { templateId, setTemplateId, templates: TEMPLATES }
  return <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>
}

export function useLayoutTemplate() {
  const ctx = useContext(LayoutContext)
  if (!ctx) throw new Error('useLayoutTemplate must be used within LayoutProvider')
  return ctx
}
