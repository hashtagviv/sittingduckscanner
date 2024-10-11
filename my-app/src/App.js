import React, { useState } from 'react';

function App() {
  const [domain, setDomain] = useState('');        
  const [domainCheckResult, setDomainCheckResult] = useState(null);  
  const [subdomains, setSubdomains] = useState([]); 

  // Function to handle domain check (registrar and lame delegation)
const handleDomainCheck = async () => {
  try {
    const response = await fetch('http://localhost:5000/api/domain-check/', {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        'Origin': 'localhost:3000'
      },
      body: JSON.stringify({ domain }),  // Send the domain to Flask API
    });

    // Check if the response is OK
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log(data); 
    setDomainCheckResult(data);  // Set the result for display
  } catch (error) {
    console.error('Error checking domain:', error);
  }
};


  // Function to handle subdomain enumeration
  const handleSubdomainEnumeration = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/subdomain-enumeration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain }),  // Send the domain to Flask API
      });

      const data = await response.json();
      setSubdomains(data.subdomains);  // Set subdomains for display
    } catch (error) {
      console.error('Error enumerating subdomains:', error);
    }
  };

  return (
    <div className="App">
      <h1>Domain and Subdomain Checker</h1>

      {/* Input for Domain */}
      <input
        type="text"
        value={domain}
        onChange={(e) => setDomain(e.target.value)}
        placeholder="Enter domain"
      />
      
      {/* Button to trigger domain check */}
      <button onClick={handleDomainCheck}>Check Domain</button>
      
      {/* Button to trigger subdomain enumeration */}
      <button onClick={handleSubdomainEnumeration}>Enumerate Subdomains</button>

      {/* Display results of domain check */}
      {domainCheckResult && (
        <div>
          <h2>Domain Check Results:</h2>
          <p>Registrar DNS Different: {domainCheckResult.registrar_dns_different.toString()}</p>
          <p>Lame Delegation: {domainCheckResult.lame_delegation.toString()}</p>
          <p>Flagged Nameservers: {domainCheckResult.flagged_nameservers.join(', ')}</p>
        </div>
      )}

      {/* Display subdomains */}
      {subdomains.length > 0 && (
        <div>
          <h2>Subdomains Found:</h2>
          <ul>
            {subdomains.map((subdomain, index) => (
              <li key={index}>{subdomain}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
