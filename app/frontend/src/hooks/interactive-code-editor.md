"use client"

import React, { useState } from "react"
import CodeMirror from "@uiw/react-codemirror"
import { javascript } from "@codemirror/lang-javascript"
import { vscodeDark } from "@uiw/codemirror-theme-vscode"
import { Card } from "@/components/ui/card"

const initialCode = `// Syntaxual Demo
function createAwesomeCode() {
  const languages = [
    "JavaScript", 
    "Python", 
    "Rust", 
    "Go"
  ];
  
  const features = {
    syntaxHighlighting: true,
    autoCompletion: true,
    themes: ["dark", "light", "synthwave"],
    cloudSync: true
  };
  
  return {
    message: "Welcome to Syntaxual!",
    supportedLanguages: languages,
    awesomeFeatures: features,
    getStarted: () => console.log("Let's code!")
  };
}

// Try it now
createAwesomeCode().getStarted();

// Start typing here...`

export default function InteractiveCodeEditor() {
  const [code, setCode] = useState(initialCode)

  const handleChange = React.useCallback((value: string) => {
    setCode(value)
  }, [])

  return (
    <Card className="border border-purple-500/30 bg-zinc-900 overflow-hidden rounded-lg shadow-lg shadow-purple-500/10">
      <div className="bg-zinc-800 px-4 py-2 border-b border-zinc-700 flex items-center justify-between">
        <div className="flex space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
        </div>
        <div className="text-xs text-white/60">syntaxual-editor.js</div>
        <div className="text-xs text-white/40">Try editing the code!</div>
      </div>
      <CodeMirror
        value={code}
        height="340px"
        theme={vscodeDark}
        extensions={[javascript({ jsx: true })]}
        onChange={handleChange}
        className="text-sm"
      />
    </Card>
  )
}
