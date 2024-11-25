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

      const response = await fetch("/message1.txt");
      const fileContent = await response.text();

      // Process file content into lines
      const lines = fileContent.split("\n").filter(Boolean);
      const parsedData = lines.map((line) => JSON.parse(line));

      // Batch loading in random groups of 3 to 10
      const batches = [];
      let index = 0;
      while (index < parsedData.length) {
        const batchSize = Math.floor(Math.random() * 8) + 3; // Random size between 3 and 10
        const batch = parsedData.slice(index, index + batchSize);
        batches.push(batch);
        index += batchSize;
      }

      const totalBatches = batches.length;
      const allNodes = [];

      const loadBatch = (batchIndex) => {
        if (batchIndex >= totalBatches) {
          setLoading(false); // All batches loaded
          setScanningCompleted(true); // Set scanning completed status
          if (intervalRef.current) {
            clearInterval(intervalRef.current); // Stop timer
          }
          return;
        }

        const batch = batches[batchIndex];

        // Compute 'vulnerable' based on 'lame_delegation' and 'registrar_dns_different'
        const newNodes = batch.map((item) => {
          const isVulnerable =
            item.lame_delegation === true &&
            item.registrar_dns_different === true;

          return {
            name: item.subdomain,
            depth: item.depth,
            vulnerable: isVulnerable,
            registrar_dns_different: item.registrar_dns_different,
            lame_delegation: item.lame_delegation,
            flagged_name_servers: item.flagged_name_servers,
            all_nameservers: item.all_nameservers,
          };
        });

        allNodes.push(...newNodes);
        setDomainData([...allNodes]); // Update the flat list of nodes

        // Update counts
        setTotalDomainsScanned((prevCount) => prevCount + newNodes.length);
        const vulnerableCount = newNodes.filter(
          (node) => node.vulnerable
        ).length;
        setTotalVulnerableDomains((prevCount) => prevCount + vulnerableCount);

        // Simulate delay for the next batch (1 to 5 seconds)
        const delay = Math.floor(Math.random() * 30000) + 8000;
        setTimeout(() => loadBatch(batchIndex + 1), delay);
      };

      // Start loading batches
      loadBatch(0);
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
