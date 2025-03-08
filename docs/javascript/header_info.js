/*
 * This file contains extra javascript code that adds elements to display metadata retrieved from the Google Docs
 * and saved in the markdown file's header
 */

document.addEventListener("DOMContentLoaded", function () {
  let metaAuthor = document.querySelector("meta[name='author']");
  let metaUpdated = document.querySelector("meta[name='updated']");

  let authorName = metaAuthor ? metaAuthor.content : "Unknown Author";
  let updatedDate = metaUpdated ? metaUpdated.content : "Unknown Date";

  let firstHeader = document.querySelector("h1, h2");

  if (firstHeader) {
    let infoTag = document.createElement("p");
    infoTag.className = "author-tag";
    infoTag.style.cssText = "font-size: 0.9em; color: #666; margin-top: -10px; font-style: italic;";
    infoTag.textContent = `Author: ${authorName} | Updated: ${updatedDate}`;

    firstHeader.insertAdjacentElement("afterend", infoTag);
  }
});
