import { useLayoutTemplate } from '../context/LayoutContext'
import ClassicLayout from './templates/ClassicLayout'
import SoftLayout from './templates/SoftLayout'

// Thin switcher: App.jsx keeps rendering <Layout /> and stays unaware that
// more than one shell exists. Each template renders its own <Outlet />.
export default function Layout() {
  const { templateId } = useLayoutTemplate()

  if (templateId === 'soft') return <SoftLayout />
  return <ClassicLayout />
}
