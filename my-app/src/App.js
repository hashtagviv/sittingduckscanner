import React, { useState, useRef } from "react";
import "./App.css";
import IndentedList from "./IndentedList";
import DomainDetails from "./DomainDetails";
import logo from "./logo.webp";

export default function App() {
  // Existing state variables...
  const [domainData, setDomainData] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(false);
  const [totalDomainsScanned, setTotalDomainsScanned] = useState(0);
  const [totalVulnerableDomains, setTotalVulnerableDomains] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [scanningCompleted, setScanningCompleted] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [showOnlyVulnerable, setShowOnlyVulnerable] = useState(false);
  const [email, setEmail] = useState("");
  const [scanType, setScanType] = useState("active");
  const [searchRelatedDomains, setSearchRelatedDomains] = useState(false);
  const [selectedTLDs, setSelectedTLDs] = useState([]);
  const [customTLDs, setCustomTLDs] = useState("");
  const [configureWeeklyEmails, setConfigureWeeklyEmails] = useState(false);

  const intervalRef = useRef(null);
  const readerRef = useRef(null);

  const handleTLDChange = (e, tld) => {
    if (e.target.checked) {
      setSelectedTLDs([...selectedTLDs, tld]);
    } else {
      setSelectedTLDs(selectedTLDs.filter((item) => item !== tld));
    }
  };

  const replaceTLD = (domain, newTLD) => {
    const parts = domain.split(".");
    if (parts.length > 1) {
      parts.pop(); // remove current TLD
      const formattedTLD = newTLD.startsWith(".") ? newTLD.slice(1) : newTLD;
      parts.push(formattedTLD);
      return parts.join(".");
    }
    return domain;
  };

  const handleStop = async () => {
    try {
      const stopResponse = await fetch("http://localhost:8000/stop", {
        method: "POST",
      });

      if (!stopResponse.ok) {
        throw new Error(`Failed to stop scanning: ${stopResponse.status}`);
      }

      setLoading(false);
      setScanningCompleted(false);
      setErrorMessage(null);

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } catch (error) {
      console.error("Error stopping scanning:", error);
      setErrorMessage(error.message || "An unexpected error occurred.");
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      setScanningCompleted(false);
      setTotalDomainsScanned(0);
      setTotalVulnerableDomains(0);
      setDomainData([]);
      setElapsedTime(0);
      setErrorMessage(null);

      intervalRef.current = setInterval(() => {
        setElapsedTime((prevTime) => prevTime + 1);
      }, 1000);

      const customTLDArray = customTLDs
        ? customTLDs
            .split(",")
            .map((tld) => tld.trim())
            .filter((tld) => tld !== "")
        : [];
      const allTLDs = [...selectedTLDs, ...customTLDArray];
      const relatedDomains = searchRelatedDomains
        ? allTLDs.map((tld) => replaceTLD(searchTerm, tld))
        : [];

      const requestBody = {
        domain: searchTerm,
        email: email,
        related_domains: relatedDomains,
        time_limit: 100000,
        active: scanType === "active" ? 1 : 0,
      };

      const startResponse = await fetch("http://localhost:8000/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!startResponse.ok) {
        throw new Error(
          `Backend server cannot process the domain: ${startResponse.status}`
        );
      }

      const streamResponse = await fetch("http://localhost:8000/stream", {
        method: "GET",
      });

      if (!streamResponse.ok) {
        throw new Error(
          `Failed to fetch stream data: ${streamResponse.status}`
        );
      }

      const reader = streamResponse.body.getReader();
      readerRef.current = reader;
      const decoder = new TextDecoder();

      let allNodes = [];
      let readFlag = true;
      while (readFlag) {
        const { value } = await reader.read();
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter(Boolean);
        const filteredLines = lines.filter((line) => line.startsWith("data:"));
        const jsonLines = filteredLines.map((line) =>
          line.replace("data: ", "")
        );
        const parsedData = jsonLines.map((jsonLine) => JSON.parse(jsonLine));

        let newNodes = [];
        for (const item of parsedData) {
          console.log(item);
          if (item.status === "complete") {
            readFlag = false;
            break;
          }

          const isVulnerable =
            item.lame_delegation === true &&
            item.registrar_dns_different === true;

          newNodes.push({
            name: item.subdomain,
            depth: item.depth,
            vulnerable: isVulnerable,
            registrar_dns_different: item.registrar_dns_different,
            lame_delegation: item.lame_delegation,
            flagged_name_servers: item.flagged_name_servers,
            all_nameservers: item.all_nameservers,
            dns_providers: item.all_orgs,
            registrar: item.registrar,
            connectivity: item.connectivity,
            issues: item.issues,
          });
        }

        allNodes.push(...newNodes);
        setDomainData([...allNodes]);

        setTotalDomainsScanned((prevCount) => prevCount + newNodes.length);
        const vulnerableCount = newNodes.filter(
          (node) => node.vulnerable
        ).length;
        setTotalVulnerableDomains((prevCount) => prevCount + vulnerableCount);
      }

      if (readerRef.current) {
        await readerRef.current.cancel();
        readerRef.current = null;
      }

      setLoading(false);
      setScanningCompleted(true);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } catch (error) {
      console.error("Error during scanning:", error);
      setLoading(false);
      setErrorMessage(error.message || "An unexpected error occurred.");
    } finally {
      if (readerRef.current) {
        await readerRef.current.cancel();
        readerRef.current = null;
      }
    }
  };

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

      {/* Configuration Box */}
      <div className="configuration-box">
        <h2>Configure Your Search</h2>
        <div className="config-items-container">
          <div className="config-item">
            <label>
              Email Results:
              <div className="tooltip-container">
                <span className="tooltip-icon">?</span>
                <span className="tooltip-text">
                  Depending on the size of your domain, it will take 5-120
                  minutes for a full scan.
                </span>
              </div>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={loading}
            />
          </div>

          <div className="config-item">
            <label>
              Scanning Type:
              <div className="tooltip-container">
                <span className="tooltip-icon">?</span>
                <span className="tooltip-text">
                  Active uses a recursive DNS brute force scan to find
                  subdomains. This may be considered malicious by the domain, we
                  recommend using passive if you do not have permission to do
                  so.
                </span>
              </div>
            </label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  value="active"
                  checked={scanType === "active"}
                  onChange={(e) => setScanType(e.target.value)}
                  disabled={loading}
                />
                Active
              </label>
              <label>
                <input
                  type="radio"
                  value="passive"
                  checked={scanType === "passive"}
                  onChange={(e) => setScanType(e.target.value)}
                  disabled={loading}
                />
                Passive
              </label>
            </div>
          </div>

          <div className="config-item">
            <label>
              <input
                type="checkbox"
                checked={searchRelatedDomains}
                onChange={(e) => setSearchRelatedDomains(e.target.checked)}
                disabled={loading}
              />
              Search for related domains
            </label>
            <label>
              <input
                type="checkbox"
                checked={configureWeeklyEmails}
                onChange={(e) => setConfigureWeeklyEmails(e.target.checked)}
                disabled={loading}
              />
              Configure weekly emails
              <div className="tooltip-container">
                <span className="tooltip-icon">?</span>
                <span className="tooltip-text">
                  Enable this for weekly reports on your domain status: It will
                  keep track of Vulnerabilities, Connectivity and New Domains!
                </span>
              </div>
            </label>
          </div>
        </div>

        {searchRelatedDomains && (
          <div className="related-domains-options">
            <div className="checkbox-group">
              {[".ca", ".org", ".co.uk", ".net", ".info", ".eu", ".ru"].map(
                (tld) => (
                  <label key={tld}>
                    <input
                      type="checkbox"
                      value={tld}
                      checked={selectedTLDs.includes(tld)}
                      onChange={(e) => handleTLDChange(e, tld)}
                      disabled={loading}
                    />
                    {tld}
                  </label>
                )
              )}
            </div>
            <div className="custom-tlds">
              <label>Custom TLDs:</label>
              <input
                type="text"
                value={customTLDs}
                onChange={(e) => setCustomTLDs(e.target.value)}
                placeholder=".net, .info"
                disabled={loading}
              />
            </div>
          </div>
        )}

        {configureWeeklyEmails && (
          <div className="weekly-emails-options">
            <div className="weekly-emails-row">
              <label>Frequency:</label>
              <span>every</span>
              <input
                type="number"
                min="1"
                style={{ width: "50px" }}
                disabled={loading}
              />

              <select disabled={loading}>
                <option>Weeks</option>
                <option>Days</option>
                <option>Months</option>
              </select>
            </div>
            <div className="weekly-email-item">
              <label></label>
              <input
                type="email"
                placeholder="Enter email"
                disabled={loading}
                style={{ width: "150px" }}
              />
              <div className="tooltip-container"></div>
            </div>
          </div>
        )}
      </div>

      <div className="search-bar">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="example.com"
        />
        <button onClick={handleSearch}>Check Domain</button>
        {loading && (
          <button onClick={handleStop} className="stop-button">
            Stop Scanning
          </button>
        )}
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
          <div className="filter-container tooltip-container">
            <label className="toggle-label">
              <input
                type="checkbox"
                className="toggle-input"
                checked={showOnlyVulnerable}
                onChange={(e) => setShowOnlyVulnerable(e.target.checked)}
              />
              <span className="toggle-slider"></span>
              <span className="tooltip-icon">?</span>
              <span className="tooltip-text">
                Enabling this will filter the domain list to show only
                vulnerable domains.
              </span>
            </label>
          </div>

          {domainData && (
            <IndentedList
              data={domainData}
              onDomainClick={setSelectedDomain}
              selectedDomain={selectedDomain}
              showOnlyVulnerable={showOnlyVulnerable}
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
      {/* Error Message Modal */}
      {errorMessage && (
        <>
          <div className="completed-overlay"></div>
          <div className="completed-box error">
            <h2>Error Occurred</h2>
            <p>{errorMessage}</p>
            <button onClick={() => setErrorMessage(null)}>Close</button>
          </div>
        </>
      )}
      {scanningCompleted && (
        <>
          <div className="completed-overlay"></div>
          <div className="completed-box">
            <h2>Scanning Completed</h2>
            <p>Total Domains Scanned: {totalDomainsScanned}</p>
            <p>Vulnerable Domains Found: {totalVulnerableDomains}</p>
            <p>Time Elapsed: {formatTime(elapsedTime)}</p>
            <button onClick={() => setScanningCompleted(false)}>Close</button>
          </div>
        </>
      )}
      <footer className="page-footer">
        If any of your domains were found to be vulnerable, then visit this
        resource for some recommended actions:
        <a
          href="https://www.cisa.gov/sites/default/files/publications/CISAInsights-Cyber-MitigateDNSInfrastructureTampering_S508C.pdf"
          target="_blank"
          rel="noopener noreferrer"
        >
          https://www.cisa.gov/sites/default/files/publications/CISAInsights-Cyber-MitigateDNSInfrastructureTampering_S508C.pdf
        </a>
      </footer>
    </div>
  );
}
