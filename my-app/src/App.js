// App.js
import React, { useState, useRef } from "react";
import "./App.css";
import IndentedList from "./IndentedList";
import DomainDetails from "./DomainDetails"; // New component
import logo from "./logo.webp";

export default function App() {
  const [domainData, setDomainData] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [totalDomainsScanned, setTotalDomainsScanned] = useState(0);
  const [totalVulnerableDomains, setTotalVulnerableDomains] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [scanningCompleted, setScanningCompleted] = useState(false); // New state variable
  const [selectedDomain, setSelectedDomain] = useState(null);

  const intervalRef = useRef(null);

  const handleSearch = async () => {
    try {
      setLoading(true);
      setScanningCompleted(false); // Reset scanning completed status
      setTotalDomainsScanned(0);
      setTotalVulnerableDomains(0);
      setDomainData([]);
      setElapsedTime(0);

      // Start timer
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      intervalRef.current = setInterval(() => {
        setElapsedTime((prevTime) => prevTime + 1);
      }, 1000);

      const startResponse = await fetch("http://localhost:8000/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          domain: searchTerm,
          time_limit: 10000,
          related_domains: [],
          active: true
        }),
      });
      
      if (!startResponse.ok) {
        throw new Error(`Backend server cannot process the domain: ${startResponse.status}`);
      }

      const streamResponse = await fetch("http://localhost:8000/stream", {
        method: "GET",
      });
  
      if (!streamResponse.ok) {
        throw new Error(`Failed to fetch stream data: ${streamResponse.status}`);
      }

      const reader = streamResponse.body.getReader();
      const decoder = new TextDecoder();
  
      let allNodes = [];
      let readFlag = true;
      while (readFlag) {
        const { value } = await reader.read();
  
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter(Boolean);
        const filteredLines = lines.filter((line) => line.startsWith("data:"));

        const jsonLines = filteredLines.map((line) => {
          return line.replace("data: ", "");
        });
 
        const parsedData = jsonLines.map((jsonLine) => {
          return JSON.parse(jsonLine);
        });

        let newNodes = [];
        for (const item of parsedData) {
          if (item.status === "complete") {
            readFlag = false; 
            break;
          }
        
          const isVulnerable =
            item.lame_delegation === true && item.registrar_dns_different === true;
        
          newNodes.push({
            name: item.subdomain,
            depth: item.depth,
            vulnerable: isVulnerable,
            registrar_dns_different: item.registrar_dns_different,
            lame_delegation: item.lame_delegation,
            flagged_name_servers: item.flagged_name_servers,
            all_nameservers: item.all_nameservers,
          });
        }
  
        allNodes.push(...newNodes);
        setDomainData([...allNodes]);
  
        // Update counts
        setTotalDomainsScanned((prevCount) => prevCount + newNodes.length);
        const vulnerableCount = newNodes.filter((node) => node.vulnerable).length;
        setTotalVulnerableDomains((prevCount) => prevCount + vulnerableCount);
      }


      setLoading(false);
      setScanningCompleted(true);

    } catch (error) {
      console.error("Error fetching or processing message.txt:", error);
      setLoading(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current); // Stop timer in case of error
      }
    }
  };

  // Function to format elapsed time in mm:ss
  const formatTime = (totalSeconds) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
  };

  return (
    <div className="App">
      <div className="title-container">
        <img src={logo} alt="Sitting Duck Detector Logo" className="logo" />
        <h1>Sitting Duck Detector</h1>
      </div>
      <div className="header-separator"></div>
      <div className="search-bar">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="example.com"
        />
        <button onClick={handleSearch}>Check Domain</button>
      </div>
      {loading && <div className="scanning-text">Scanning...</div>}
      <div className="status-bar">
        <span>Domains Scanned: {totalDomainsScanned}</span>
        <span>Vulnerable Domains Found: {totalVulnerableDomains}</span>
        {totalDomainsScanned > 0 && (
          <span>Time Elapsed: {formatTime(elapsedTime)}</span>
        )}
      </div>
      <div className="content-container">
        <div className="left-pane">
          <h2>Domain List</h2>
          {domainData && (
            <IndentedList
              data={domainData}
              onDomainClick={setSelectedDomain}
              selectedDomain={selectedDomain}
            />
          )}
        </div>
        <div className="right-pane">
          {selectedDomain ? (
            <DomainDetails domain={selectedDomain} />
          ) : (
            <p>Select a domain to see details.</p>
          )}
        </div>
      </div>
      {scanningCompleted && (
        <>
          <div className="completed-overlay"></div>
          <div className="completed-box">
            <h2>Scanning Completed</h2>
            <p>Total Domains Scanned: {totalDomainsScanned}</p>
            <p>Vulnerable Domains Found: {totalVulnerableDomains}</p>
            <button onClick={() => setScanningCompleted(false)}>Close</button>
          </div>
        </>
      )}
    </div>
  );
}
