/**
 * ⚡ JARVIS Code Execution Engine — Write & Run Any Code
 * ═══════════════════════════════════════════════════════
 * 
 * Supports running code in:
 * - JavaScript (browser sandbox)
 * - Python (via desktop IPC or Pyodide WASM)
 * - HTML/CSS (iframe sandbox)
 * - Shell commands (desktop only)
 * 
 * Desktop mode: Runs natively via Electron IPC
 * Web mode: Uses Web Workers + Pyodide for Python
 */

class CodeExecutionEngine {
  constructor() {
    try {
        this.isDesktop = !!window.jarvisDesktop
      this.pyodideReady = false
      this.pyodide = null
      this.runningProcesses = new Map()
      this.executionHistory = []
      this.maxHistory = 50
  
    } catch(e) {
      console.warn('[codeExecutionEngine] Constructor init error:', e)
    }
}

  /**
   * Execute code in specified language
   */
  async execute(code, language = 'javascript', options = {}) {
    const startTime = performance.now()
    let result

    try {
      switch (language.toLowerCase()) {
        case 'javascript':
        case 'js':
          result = await this._runJavaScript(code, options)
          break

        case 'python':
        case 'py':
          result = await this._runPython(code, options)
          break

        case 'html':
          result = await this._runHTML(code, options)
          break

        case 'shell':
        case 'bash':
        case 'cmd':
        case 'terminal':
          result = await this._runShell(code, options)
          break

        case 'typescript':
        case 'ts':
          result = await this._runTypeScript(code, options)
          break

        default:
          // Try desktop execution for any language
          if (this.isDesktop) {
            result = await this._runViaDesktop(code, language, options)
          } else {
            result = { success: false, error: `Language '${language}' is only supported in desktop mode` }
          }
      }
    } catch (err) {
      result = { success: false, error: err.message, output: '' }
    }

    const elapsed = performance.now() - startTime
    const entry = { code, language, result, elapsed, timestamp: Date.now() }
    this.executionHistory.push(entry)
    if (this.executionHistory.length > this.maxHistory) {
      this.executionHistory.shift()
    }

    return { ...result, elapsed: `${elapsed.toFixed(0)}ms` }
  }

  /**
   * Run JavaScript in sandboxed Web Worker
   */
  async _runJavaScript(code, options = {}) {
    return new Promise((resolve) => {
      const timeout = options.timeout || 10000

      const workerCode = `
        self.onmessage = function(e) {
          const logs = [];
          const originalLog = console.log;
          console.log = (...args) => logs.push(args.map(a => typeof a === 'object' ? JSON.stringify(a, null, 2) : String(a)).join(' '));
          console.error = (...args) => logs.push('[ERROR] ' + args.map(String).join(' '));
          console.warn = (...args) => logs.push('[WARN] ' + args.map(String).join(' '));
          
          try {
            const result = eval(e.data);
            const output = logs.join('\\n');
            const returnVal = result !== undefined ? (typeof result === 'object' ? JSON.stringify(result, null, 2) : String(result)) : '';
            self.postMessage({ success: true, output: output + (output && returnVal ? '\\n' : '') + returnVal });
          } catch (err) {
            const output = logs.join('\\n');
            self.postMessage({ success: false, error: err.message, output });
          }
        };
      `

      const blob = new Blob([workerCode], { type: 'application/javascript' })
      const worker = new Worker(URL.createObjectURL(blob))

      const timer = setTimeout(() => {
        worker.terminate()
        resolve({ success: false, error: 'Execution timed out (10s)', output: '' })
      }, timeout)

      worker.onmessage = (e) => {
        clearTimeout(timer)
        worker.terminate()
        resolve(e.data)
      }

      worker.onerror = (err) => {
        clearTimeout(timer)
        worker.terminate()
        resolve({ success: false, error: err.message, output: '' })
      }

      worker.postMessage(code)
    })
  }

  /**
   * Run Python — Desktop: native, Web: Pyodide WASM
   */
  async _runPython(code, options = {}) {
    // Desktop mode — run natively
    if (this.isDesktop) {
      return this._runViaDesktop(code, 'python', options)
    }

    // Web mode — use Pyodide (Python in WASM)
    if (!this.pyodideReady) {
      await this._loadPyodide()
    }

    if (!this.pyodide) {
      // Fallback: try to run simple Python via eval translation
      return this._pythonFallback(code)
    }

    try {
      // Capture stdout
      this.pyodide.runPython(`
import sys, io
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
      `)

      const result = this.pyodide.runPython(code)
      const stdout = this.pyodide.runPython('sys.stdout.getvalue()')
      const stderr = this.pyodide.runPython('sys.stderr.getvalue()')

      const output = [stdout, result !== undefined && result !== null ? String(result) : '', stderr].filter(Boolean).join('\n')

      return { success: !stderr, output, error: stderr || null }
    } catch (err) {
      return { success: false, error: err.message, output: '' }
    }
  }

  /**
   * Load Pyodide (Python WASM runtime)
   */
  async _loadPyodide() {
    try {
      if (typeof loadPyodide === 'undefined') {
        // Dynamically load Pyodide
        const script = document.createElement('script')
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js'
        document.head.appendChild(script)
        
        await new Promise((resolve, reject) => {
          script.onload = resolve
          script.onerror = reject
          setTimeout(reject, 15000)
        })
      }

      this.pyodide = await window.loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.25.1/full/'
      })
      this.pyodideReady = true
      console.log('[CodeEngine] Pyodide loaded — Python ready in browser')
    } catch (err) {
      console.warn('[CodeEngine] Pyodide load failed:', err)
      this.pyodideReady = true // Mark as attempted
    }
  }

  /**
   * Simple Python fallback (basic expressions)
   */
  _pythonFallback(code) {
    try {
      // Handle very basic Python patterns
      const lines = code.trim().split('\n')
      let output = []

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || trimmed.startsWith('#')) continue

        // print() statements
        const printMatch = trimmed.match(/^print\((.+)\)$/)
        if (printMatch) {
          try {
            const val = eval(printMatch[1].replace(/f"/g, '`').replace(/"/g, '"'))
            output.push(String(val))
          } catch {
            output.push(printMatch[1].replace(/['"]/g, ''))
          }
          continue
        }
      }

      if (output.length > 0) {
        return { success: true, output: output.join('\n') }
      }

      return { 
        success: false, 
        error: 'Python execution requires Pyodide (loading...) or Desktop mode. Basic print() statements work in web mode.',
        output: '' 
      }
    } catch (err) {
      return { success: false, error: err.message, output: '' }
    }
  }

  /**
   * Run HTML in iframe sandbox
   */
  async _runHTML(code, options = {}) {
    try {
      const iframe = document.createElement('iframe')
      iframe.sandbox = 'allow-scripts'
      iframe.style.cssText = 'width:100%;height:400px;border:1px solid rgba(0,212,255,0.3);border-radius:8px;background:#fff;'
      
      const blob = new Blob([code], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      
      return { 
        success: true, 
        output: 'HTML rendered successfully',
        htmlUrl: url,
        htmlCode: code
      }
    } catch (err) {
      return { success: false, error: err.message, output: '' }
    }
  }

  /**
   * Run shell commands (Desktop only)
   */
  async _runShell(code, options = {}) {
    if (!this.isDesktop) {
      return { 
        success: false, 
        error: 'Shell commands require Desktop mode (Electron)',
        output: '' 
      }
    }

    try {
      const result = await window.jarvisDesktop.runCommand(code)
      return {
        success: result.success,
        output: result.stdout || '',
        error: result.stderr || result.error || null
      }
    } catch (err) {
      return { success: false, error: err.message, output: '' }
    }
  }

  /**
   * Run TypeScript (transpile to JS first)
   */
  async _runTypeScript(code, options = {}) {
    // Strip type annotations for basic execution
    const jsCode = code
      .replace(/:\s*(string|number|boolean|any|void|object|Array<[^>]+>|Record<[^>]+>)\s*/g, ' ')
      .replace(/interface\s+\w+\s*\{[^}]*\}/g, '')
      .replace(/type\s+\w+\s*=\s*[^;]+;/g, '')
      .replace(/<[^>]+>/g, '')
      .replace(/as\s+\w+/g, '')

    return this._runJavaScript(jsCode, options)
  }

  /**
   * Run any language via Desktop (Electron IPC)
   */
  async _runViaDesktop(code, language, options = {}) {
    if (!this.isDesktop) {
      return { success: false, error: 'Desktop mode required for ' + language, output: '' }
    }

    // Map language to execution command
    const langCommands = {
      python: (code) => {
        // Write to temp file and execute
        const tmpFile = `/tmp/jarvis_exec_${Date.now()}.py`
        return { writeFile: tmpFile, command: `python3 "${tmpFile}"` }
      },
      node: (code) => {
        const tmpFile = `/tmp/jarvis_exec_${Date.now()}.js`
        return { writeFile: tmpFile, command: `node "${tmpFile}"` }
      },
      ruby: (code) => {
        const tmpFile = `/tmp/jarvis_exec_${Date.now()}.rb`
        return { writeFile: tmpFile, command: `ruby "${tmpFile}"` }
      },
      go: (code) => {
        const tmpFile = `/tmp/jarvis_exec_${Date.now()}.go`
        return { writeFile: tmpFile, command: `go run "${tmpFile}"` }
      },
      rust: (code) => {
        const tmpFile = `/tmp/jarvis_exec_${Date.now()}.rs`
        return { writeFile: tmpFile, command: `rustc "${tmpFile}" -o /tmp/jarvis_exec && /tmp/jarvis_exec` }
      },
      java: (code) => {
        const tmpFile = `/tmp/JarvisExec.java`
        return { writeFile: tmpFile, command: `cd /tmp && javac JarvisExec.java && java JarvisExec` }
      },
      cpp: (code) => {
        const tmpFile = `/tmp/jarvis_exec_${Date.now()}.cpp`
        return { writeFile: tmpFile, command: `g++ "${tmpFile}" -o /tmp/jarvis_exec && /tmp/jarvis_exec` }
      },
      c: (code) => {
        const tmpFile = `/tmp/jarvis_exec_${Date.now()}.c`
        return { writeFile: tmpFile, command: `gcc "${tmpFile}" -o /tmp/jarvis_exec && /tmp/jarvis_exec` }
      }
    }

    const langKey = language.toLowerCase().replace('python3', 'python').replace('py', 'python').replace('js', 'node').replace('javascript', 'node')
    const cmdConfig = langCommands[langKey]

    if (!cmdConfig) {
      // Try direct execution
      return this._runShell(code, options)
    }

    try {
      const { writeFile, command } = cmdConfig(code)
      
      // Write code to temp file
      await window.jarvisDesktop.writeFile(writeFile, code)
      
      // Execute
      const result = await window.jarvisDesktop.runCommand(command)
      
      // Cleanup
      window.jarvisDesktop.deleteFile(writeFile).catch(() => {})
      
      return {
        success: result.success,
        output: result.stdout || '',
        error: result.stderr || result.error || null
      }
    } catch (err) {
      return { success: false, error: err.message, output: '' }
    }
  }

  /**
   * Get supported languages
   */
  getSupportedLanguages() {
    const webLanguages = [
      { id: 'javascript', name: 'JavaScript', icon: '📜', available: true },
      { id: 'python', name: 'Python', icon: '🐍', available: true, note: this.isDesktop ? 'Native' : 'Pyodide WASM' },
      { id: 'html', name: 'HTML/CSS', icon: '🌐', available: true },
      { id: 'typescript', name: 'TypeScript', icon: '📘', available: true },
    ]

    const desktopLanguages = this.isDesktop ? [
      { id: 'shell', name: 'Shell/Bash', icon: '💻', available: true },
      { id: 'go', name: 'Go', icon: '🔵', available: true },
      { id: 'rust', name: 'Rust', icon: '🦀', available: true },
      { id: 'java', name: 'Java', icon: '☕', available: true },
      { id: 'cpp', name: 'C++', icon: '⚙️', available: true },
      { id: 'c', name: 'C', icon: '🔧', available: true },
      { id: 'ruby', name: 'Ruby', icon: '💎', available: true },
    ] : []

    return [...webLanguages, ...desktopLanguages]
  }

  /**
   * Get execution history
   */
  getHistory() {
    return this.executionHistory
  }

  /**
   * Clear history
   */
  clearHistory() {
    this.executionHistory = []
  }

  /**
   * Install Python package (via Pyodide micropip)
   */
  async installPythonPackage(packageName) {
    if (this.isDesktop) {
      return this._runShell(`pip install ${packageName}`)
    }

    if (!this.pyodide) {
      return { success: false, error: 'Pyodide not loaded' }
    }

    try {
      await this.pyodide.loadPackage('micropip')
      const micropip = this.pyodide.pyimport('micropip')
      await micropip.install(packageName)
      return { success: true, output: `Package '${packageName}' installed successfully` }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }
}

const codeEngine = new CodeExecutionEngine()
export default codeEngine
