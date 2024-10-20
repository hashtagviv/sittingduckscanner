import React, { useState, useEffect } from 'react';
import * as d3 from 'd3';
import './App.css';

const TreeChart = ({ data }) => {
  const svgRef = React.useRef();
  const tooltipRef = React.useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    const tooltip = d3.select(tooltipRef.current);
    svg.selectAll("*").remove(); 

    const width = 900;
    const height = 700;

    const root = d3.hierarchy(data);
    const treeLayout = d3.tree().size([width - 200, height - 200]);
    treeLayout(root);

    const g = svg.append("g").attr("transform", "translate(100, 50)");

    
    g.selectAll('path')
      .data(root.links())
      .enter()
      .append('path')
      .attr('d', d3.linkHorizontal().x(d => d.y).y(d => d.x))
      .attr('fill', 'none')
      .attr('stroke', '#ccc');

    
    const nodes = g.selectAll('g.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('transform', d => `translate(${d.y}, ${d.x})`)
      .on('mouseover', (event, d) => {
        tooltip.style('display', 'block');
        tooltip.html(`<strong>Domain:</strong> ${d.data.name}<br/><strong>Depth:</strong> ${d.depth}<br/><strong>Vulnerable:</strong> ${d.data.vulnerable ? 'Yes' : 'No'}`);
      })
      .on('mousemove', (event) => {
        tooltip.style('left', (event.pageX + 15) + 'px').style('top', (event.pageY - 15) + 'px');
      })
      .on('mouseout', () => {
        tooltip.style('display', 'none');
      });

    
    nodes.append('circle')
      .attr('r', 25)
      .attr('fill', d => d.data.vulnerable ? 'red' : 'lightgreen')
      .attr('stroke', 'black');

    
    nodes.append('text')
      .attr('dx', 30)
      .attr('dy', 5)
      .style('font-size', '24px')
      .text(d => d.data.name);

  }, [data]);

  return (
    <div>
      <svg ref={svgRef} width={900} height={700} className="tree-chart"></svg>
      <div ref={tooltipRef} className="tooltip"></div> {/* Tooltip */}
    </div>
  );
};

export default function App() {
  const [domainData, setDomainData] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  const handleSearch = async () => {
    try {
      
      const response = await fetch('http://localhost:5001/domainData'); 
      const data = await response.json();

    
      const domainDataTree = {
        name: searchTerm,
        vulnerable: false,
        children: data.map(item => ({
          name: item.subdomain,
          vulnerable: item.lame_delegation,
          children: item.flagged_name_servers.map(ns => ({
            name: ns,
            vulnerable: true
          }))
        }))
      };

      setDomainData(domainDataTree);
    } catch (error) {
      console.error("Error fetching domain data:", error);
    }
  };

  return (
    <div className="App">
      <div className="title-container">
        <h1>Domain and Subdomain Checker</h1>
      </div>
      <div className="search-bar">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="example.com"
        />
        <button onClick={handleSearch}>Check Domain</button>
      </div>
      <div className="content-container">
        <div className="info-panel">
          {domainData && (
            <div>
              <h2>Subdomain List:</h2>
              <p><strong>Subdomain:</strong> {domainData.name}</p>
              <p><strong>Depth:</strong> 0</p>
              <p><strong>Vulnerable:</strong> No</p>
              <p><strong>Flagged Name Servers:</strong> None</p>
              {domainData.children.map((child, index) => (
                <div key={index}>
                  <p><strong>Subdomain:</strong> {child.name}</p>
                  <p><strong>Depth:</strong> 1</p>
                  <p><strong>Vulnerable:</strong> {child.vulnerable ? 'Yes' : 'No'}</p>
                  <p><strong>Flagged Name Servers:</strong> {child.children.map(ns => ns.name).join(', ')}</p>
                </div>
              ))}
            </div>
          )}
        </div>
        <div>
          {domainData && <TreeChart data={domainData} />}
        </div>
      </div>
    </div>
  );
}
