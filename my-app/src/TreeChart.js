import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const TreeChart = ({ data }) => {
  const svgRef = useRef();
  const tooltipRef = useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous SVG

    const width = 300;
    const height = 500;

    // Create root hierarchy
    const root = d3.hierarchy(data);
    root.x0 = height / 2;
    root.y0 = 0;

    // Tree layout with fixed size
    const treeLayout = d3.tree().size([height, width]); // Reduced horizontal spacing

    const g = svg.append("g").attr("transform", "translate(100, 50)");

    // Generate tree layout
    treeLayout(root);

    // Add links between nodes
    const links = g
      .selectAll("path.link")
      .data(root.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr(
        "d",
        d3
          .linkHorizontal()
          .x((d) => d.y)
          .y((d) => d.x)
      )
      .attr("fill", "none")
      .attr("stroke", "#ccc")
      .attr("stroke-width", 1);

    // Add nodes
    const nodes = g
      .selectAll("g.node")
      .data(root.descendants())
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", (d) => `translate(${d.y}, ${d.x})`)
      .on("mouseover", (event, d) => {
        const tooltip = d3.select(tooltipRef.current);
        const nodeBox = event.target.getBoundingClientRect(); // Get the position of the hovered node
        tooltip
          .style("display", "block")
          .style("left", `${nodeBox.right + 10}px`) // Place tooltip 10px to the right of the node
          .style("top", `${nodeBox.top + window.scrollY}px`) // Align vertically with the node
          .html(`
            <strong>Domain:</strong> ${d.data.name}<br/>
            <strong>Depth:</strong> ${d.depth}<br/>
            <strong>Registrar DNS Different:</strong> ${
              d.data.registrar_dns_different ? "Yes" : "No"
            }<br/>
            <strong>Lame Delegation:</strong> ${
              d.data.lame_delegation ? "Yes" : "No"
            }<br/>
            <strong>Vulnerable:</strong> ${
              d.data.vulnerable ? "Yes" : "No"
            }<br/>
          `);
      })
      .on("mouseout", () => {
        const tooltip = d3.select(tooltipRef.current);
        tooltip.style("display", "none");
      });

    // Add circles for nodes
    nodes
      .append("circle")
      .attr("r", 10)
      .attr("fill", (d) => (d.data.vulnerable ? "red" : "lightgreen"));

    // Add text labels for nodes
    nodes
      .append("text")
      .attr("dx", 15) // Space text away from the circle horizontally
      .attr("dy", 5) // Align text with the center of the circle vertically
      .text((d) => d.data.name)
      .style("font-size", "12px");
  }, [data]);

  return (
    <div style={{ position: "relative" }}>
      <svg ref={svgRef} width={900} height={700}></svg>
      <div
        ref={tooltipRef}
        style={{
          position: "absolute",
          display: "none",
          backgroundColor: "white",
          border: "1px solid #ccc",
          borderRadius: "4px",
          padding: "5px",
          pointerEvents: "none",
          fontSize: "12px",
          boxShadow: "0px 2px 4px rgba(0, 0, 0, 0.2)",
        }}
      ></div>
    </div>
  );
};

export default TreeChart;
