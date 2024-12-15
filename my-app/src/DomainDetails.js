// DomainDetails.js
import React, { useState } from "react";
import "./DomainDetails.css";

const DomainDetails = ({ domain }) => {
  const isVulnerable = domain.vulnerable;
  const [isLameDelegationOpen, setIsLameDelegationOpen] = useState(false);

  const toggleLameDelegation = () => {
    setIsLameDelegationOpen(!isLameDelegationOpen);
  };
  const connectivityText = domain.connectivity ? "Success" : "Failed";
  const connectivityClass = domain.connectivity
    ? "connectivity-success"
    : "connectivity-failure";

  return (
    <div className="domain-details">
      <h2 className={`domain-status ${isVulnerable ? "vulnerable" : "safe"}`}>
        {isVulnerable ? "POSSIBLY VULNERABLE DOMAIN" : "Safe Domain"}
      </h2>
      <div
        className={`domain-name-box ${isVulnerable ? "vulnerable" : "safe"}`}
      >
        <h3>Domain</h3>
        <p>{domain.name}</p>
        <p className="registrar-info">Registrar: {domain.registrar}</p>
        <p>
          Connectivity:{" "}
          <span className={connectivityClass}>{connectivityText}</span>
        </p>
      </div>
      <div className="domain-info">
        {/* Lame Delegation Section */}
        <div
          className={`status-box ${
            domain.lame_delegation ? "warning" : "good"
          }`}
        >
          <div
            className="status-box-header"
            onClick={domain.lame_delegation ? toggleLameDelegation : undefined}
            style={{ cursor: domain.lame_delegation ? "pointer" : "default" }}
          >
            <strong>Is it using lame delegation?</strong>
            <span className="status-indicator">
              {domain.lame_delegation ? "Yes" : "No"}
            </span>
            {domain.lame_delegation && (
              <span
                className={`arrow ${isLameDelegationOpen ? "open" : ""}`}
              ></span>
            )}
          </div>
          {domain.lame_delegation && isLameDelegationOpen && (
            <div className="status-box-content">
              <p>
                <a
                  href="https://blogs.infoblox.com/threat-intelligence/who-knew-domain-hijacking-is-so-easy/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Learn more about the risks of lame delegation DNS resolution.
                </a>
              </p>
              <h4>Issues:</h4>
              {domain.issues && Object.keys(domain.issues).length > 0 ? (
                Object.entries(domain.issues).map(([nameserver, issues]) => (
                  <div key={nameserver}>
                    <strong>Nameserver : {nameserver}</strong>
                    <ul>
                      {issues.map((issue, index) => (
                        <li key={index}>{issue}</li>
                      ))}
                    </ul>
                    <a
                      href="issues.html"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      How can I fix this?
                    </a>
                  </div>
                ))
              ) : (
                <p>No specific issues found.</p>
              )}
            </div>
          )}
        </div>

        {/* Registrar DNS Different Section */}
        <div
          className={`status-box ${
            domain.registrar_dns_different ? "warning" : "good"
          }`}
        >
          <div className="status-box-header">
            <strong>Are the DNS provider and Registrar different?</strong>
            <span className="status-indicator">
              {domain.registrar_dns_different ? "Yes" : "No"}
            </span>
          </div>
        </div>

        <h3>Nameservers</h3>
        <table className="nameservers-table">
          <thead>
            <tr>
              <th>Nameserver</th>
              <th>DNS Provider</th>
            </tr>
          </thead>
          <tbody>
            {domain.all_nameservers.map((ns, index) => (
              <tr
                key={index}
                className={
                  domain.flagged_name_servers &&
                  domain.flagged_name_servers.includes(ns)
                    ? "flagged-nameserver"
                    : ""
                }
              >
                <td>{ns}</td>
                <td>{domain.dns_providers[index] || "Unknown"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DomainDetails;
