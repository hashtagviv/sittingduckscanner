// IndentedList.js
import React from "react";
import "./IndentedList.css";

const IndentedList = ({ data, onDomainClick, selectedDomain }) => {
  return (
    <div className="indented-list">
      {data.map((node, index) => (
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
