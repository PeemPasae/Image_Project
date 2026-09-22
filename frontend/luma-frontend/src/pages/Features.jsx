import { useState } from 'react'
import FeatureTabs from '../components/features/FeatureTabs'
import SpotBlurTool from '../components/features/SpotBlurTool'
import '../styles/features.css'

// Grid of feature cards that morphs (FLIP) into a folder-style tab bar with
// the selected tool's panel attached underneath. Only Spot Blur exists so far.
export default function Features() {
  const [expanded, setExpanded] = useState(false)

  return (
    <div>
      <div className="page-header">
        <h1>Features</h1>
        <p>{expanded ? 'Pick a spot, blur it.' : 'Image tools for your generations — more on the way.'}</p>
      </div>

      <FeatureTabs
        expanded={expanded}
        onSelect={(id) => { if (id === 'spot-blur') setExpanded(true) }}
        onBack={() => setExpanded(false)}
      />

      {expanded && (
        <div className="feature-panel">
          <SpotBlurTool />
        </div>
      )}
    </div>
  )
}
