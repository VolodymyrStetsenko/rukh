"use client"

import { useState } from "react"
import { Upload, FileCode, Play, Download, Github } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleAnalyze = async () => {
    if (!file) return
    setAnalyzing(true)
    setTimeout(() => {
      setAnalyzing(false)
    }, 3000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">R</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">RUKH</h1>
              <p className="text-xs text-slate-400">AI-powered Smart Contract Audit</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/VolodymyrStetsenko/rukh"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-white transition-colors"
            >
              <Github className="w-6 h-6" />
            </a>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold text-white mb-4">
            Red-Team AI for Smart Contracts
          </h2>
          <p className="text-xl text-slate-300 mb-2">
            Think like black-hat, act white-hat.
          </p>
          <p className="text-sm text-slate-400">
            By Volodymyr Stetsenko (Zero2Auditor)
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-8 shadow-2xl">
            <div className="mb-6">
              <h3 className="text-2xl font-semibold text-white mb-2">
                Upload Smart Contract
              </h3>
              <p className="text-slate-400">
                Upload your Solidity contract or provide a repository URL for comprehensive analysis
              </p>
            </div>

            <div className="border-2 border-dashed border-slate-600 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".sol,.zip"
                onChange={handleFileUpload}
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-16 h-16 mx-auto mb-4 text-slate-400" />
                {file ? (
                  <div>
                    <p className="text-white font-medium mb-2">{file.name}</p>
                    <p className="text-sm text-slate-400">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-white font-medium mb-2">
                      Drop your contract here or click to browse
                    </p>
                    <p className="text-sm text-slate-400">
                      Supports .sol files and .zip archives
                    </p>
                  </div>
                )}
              </label>
            </div>

            <div className="mt-6 flex gap-4">
              <Button
                onClick={handleAnalyze}
                disabled={!file || analyzing}
                className="flex-1 h-12 text-base bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
              >
                {analyzing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="mr-2" />
                    Start Analysis
                  </>
                )}
              </Button>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <FileCode className="w-10 h-10 text-blue-400 mb-4" />
              <h4 className="text-lg font-semibold text-white mb-2">
                Static Analysis
              </h4>
              <p className="text-sm text-slate-400">
                AST/CFG/DFG parsing, role detection, SWC detectors with Slither & Aderyn
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <Play className="w-10 h-10 text-purple-400 mb-4" />
              <h4 className="text-lg font-semibold text-white mb-2">
                Fuzzing & Symbolic
              </h4>
              <p className="text-sm text-slate-400">
                Coverage-guided fuzzing, invariant testing, symbolic execution with Z3
              </p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
              <Download className="w-10 h-10 text-green-400 mb-4" />
              <h4 className="text-lg font-semibold text-white mb-2">
                Test Generation
              </h4>
              <p className="text-sm text-slate-400">
                Auto-generate Foundry test suites with PoCs ready for export
              </p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-700 mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-slate-400 text-sm">
            <p className="mb-2">
              © 2025 Volodymyr Stetsenko. Licensed under MIT.
            </p>
            <p className="text-xs text-slate-500">
              Authorization required. Use only on contracts you own or have permission to audit.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
