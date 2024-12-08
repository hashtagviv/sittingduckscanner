// IndentedList.js
import React from "react";
import "./IndentedList.css";

const IndentedList = ({
  data,
  onDomainClick,
  selectedDomain,
  showOnlyVulnerable,
}) => {
  const getAncestors = (domainName) => {
    const parts = domainName.split(".");
    const ancestors = [];
    for (let i = 1; i < parts.length; i++) {
      const ancestor = parts.slice(i).join(".");
      ancestors.push(ancestor);
    }
    return ancestors;
  };

  // Apply filtering
  let filteredData = data;
  if (showOnlyVulnerable) {
    const vulnerableDomains = data.filter((domain) => domain.vulnerable);
    const vulnerableDomainNames = new Set(
      vulnerableDomains.map((domain) => domain.name)
    );

    const ancestorDomainNames = new Set();
    vulnerableDomains.forEach((domain) => {
      const ancestors = getAncestors(domain.name);
      ancestors.forEach((ancestor) => {
        ancestorDomainNames.add(ancestor);
      });
    });

    filteredData = data.filter(
      (domain) =>
        vulnerableDomainNames.has(domain.name) ||
        ancestorDomainNames.has(domain.name)
    );
  }

  return (
    <div className="indented-list">
      {filteredData.map((node, index) => (
        <div
          key={index}
          className={`node-item depth-${node.depth} ${
            node.vulnerable ? "vulnerable" : "safe"
          } ${
            selectedDomain && selectedDomain.name === node.name
              ? "selected"
              : ""
          }`}
          title={`Depth: ${node.depth}, Vulnerable: ${
            node.vulnerable ? "Yes" : "No"
          }`}
          onClick={() => onDomainClick(node)}
        >
          <span
            className={`node-bubble ${node.vulnerable ? "vulnerable" : "safe"}`}
          ></span>
          <span className={`node-name ${node.depth === 0 ? "root-node" : ""}`}>
            {node.name}
          </span>
        </div>
      ))}
    </div>
  );
};

export default IndentedList;
