class c{constructor(){var e;this.isNative=typeof window<"u"&&((e=window.Capacitor)==null?void 0:e.isNativePlatform()),this.recognition=null,this.synth=window.speechSynthesis||null,this.chatHistory=[]}get isWeb(){return!this.isNative}async startWebSTT(e,i){const n=window.SpeechRecognition||window.webkitSpeechRecognition;if(!n)throw new Error("Speech Recognition not supported in this browser");this.recognition=new n,this.recognition.continuous=!0,this.recognition.interimResults=!0,this.recognition.lang="hi-IN",this.recognition.onresult=t=>{let a="",s="";for(let r=t.resultIndex;r<t.results.length;r++){const o=t.results[r][0].transcript;t.results[r].isFinal?a+=o+" ":s+=o}s&&i&&i(s),a&&e&&e(a.trim())},this.recognition.onerror=t=>{console.warn("Web STT error:",t.error)},this.recognition.start()}stopWebSTT(){this.recognition&&(this.recognition.stop(),this.recognition=null)}async speakWeb(e,i={}){var r;if(!this.synth)return;this.synth.cancel();const n=new SpeechSynthesisUtterance(e);n.lang=i.language||"hi-IN",n.rate=i.rate||1,n.pitch=i.pitch||1;const t=this.synth.getVoices(),a=t.find(o=>o.lang.includes("hi")),s=t.find(o=>o.lang.includes("en-IN"));return(r=i.language)!=null&&r.includes("hi")&&a?n.voice=a:s&&(n.voice=s),new Promise(o=>{n.onend=o,this.synth.speak(n)})}stopWebTTS(){this.synth&&this.synth.cancel()}async mockBattery(){if(navigator.getBattery){const e=await navigator.getBattery();return{level:Math.round(e.level*100),isCharging:e.charging,chargingType:e.charging?"USB":"None",temperature:28.5,status:e.charging?"Charging":"Discharging"}}return{level:75,isCharging:!1,chargingType:"None",temperature:30,status:"Discharging"}}async mockNetwork(){var e;return{connected:navigator.onLine,type:((e=navigator.connection)==null?void 0:e.type)||"WiFi",wifiEnabled:!0,ssid:"Unknown (Web mode)"}}async mockDeviceInfo(){var e;return{brand:"Web Browser",model:((e=navigator.userAgent.split("(")[1])==null?void 0:e.split(")")[0])||"Unknown",androidVersion:"N/A (Web)",processors:navigator.hardwareConcurrency||4,maxMemoryMB:"N/A"}}async mockDateTime(){const e=new Date;return{date:e.toLocaleDateString("hi-IN",{day:"2-digit",month:"long",year:"numeric"}),time:e.toLocaleTimeString("hi-IN",{hour:"2-digit",minute:"2-digit",hour12:!0}),day:e.toLocaleDateString("hi-IN",{weekday:"long"}),full:e.toLocaleString("hi-IN"),timestamp:e.getTime()}}async mockGenerate(e){const i=e.toLowerCase(),n={"hello|hi|hey|namaste|namaskar":"Namaste! 🙏 Main JARVIS hoon. Kaise madad kar sakta hoon? (Note: Yeh web mode hai — phone pe full AI chalega)",battery:`🔋 Battery Info:
${JSON.stringify(await this.mockBattery(),null,2)}

*Web mode mein real battery API use ho raha hai*`,"time|samay|waqt":`🕐 ${new Date().toLocaleString("hi-IN")}

*Phone pe zyada accurate hoga with timezone*`,"network|wifi|internet":`📶 Online: ${navigator.onLine?"Yes ✅":"No ❌"}

*Phone pe full WiFi/cellular details milenge*`,"device|phone":`📱 Browser: ${navigator.userAgent.substring(0,50)}...
Cores: ${navigator.hardwareConcurrency}

*Phone pe full device info milega*`,"joke|mazak":'😄 Ek programmer ne apni maa se kaha: "Maa, mujhe ek girlfriend chahiye." Maa boli: "Beta, pehle bugs to fix kar le!" 😂',"market|nifty|bitcoin|btc":`📊 Market data ke liye internet chahiye. Offline mode mein saved data use hoga.

Tip: Phone pe JARVIS AI Agent install karo — trading features bhi milenge! 🚀`};for(const[t,a]of Object.entries(n))if(new RegExp(t,"i").test(i))return{text:a,model:"web-mock",tokensUsed:0};return{text:`🌐 **Web Mode Response**

Aapne kaha: "${e}"

Yeh web/browser mode hai — basic responses hi milenge.

📱 **Full AI ke liye:**
1. APK build karo: \`bash build_apk_ai_agent.sh\`
2. Phone pe install karo
3. LLM model download karo
4. Phir offline AI full power se chalega! 🧠

*Jai Mahadev! 🙏*`,model:"web-mock",tokensUsed:0}}}const l=new c;export{l as default};
