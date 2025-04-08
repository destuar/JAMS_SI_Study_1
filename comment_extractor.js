/**
 * Facebook Comment Extractor Snippet for Browser Console
 *
 * ACTION NEEDED: Testing revised safeGetText function using querySelectorAll.
 */
(function() {
    console.log("Starting comment extraction...");
    const comments = [];

    // --- SELECTORS ---
    const commentSelector = 'div[role="article"]';
    // const authorSelector = 'span > a[role="link"][aria-label]'; // Removed author selector
    const timestampSelector = 'a[href*="comment_id="]';
    // Selector for potential text containers (we'll filter results)
    const potentialTextSelector = 'div[dir="auto"]';
    // Selector for reaction count button
    const reactionSelector = 'div[role="button"][aria-label*=" reaction"]'; // Note the space before reaction

    // --- REVISED FUNCTION to extract text using querySelectorAll ---
    /**
     * Safely extracts the main text content from a comment element.
     * @param {Element} element - The comment's root DOM element (matching commentSelector).
     * @returns {{text: string|null, node: Element|null}} Object with extracted text and the node it came from.
     */
    function safeGetText(element) {
        // Find ALL potential text nodes within the comment element using the defined selector.
        const potentialTextNodes = element.querySelectorAll(potentialTextSelector);
        let bestText = null; // Store the most likely comment text found.
        let bestNode = null; // Store the DOM node corresponding to bestText.

        if (potentialTextNodes.length > 0) {
            // Iterate through all found potential text nodes.
            potentialTextNodes.forEach(node => {
                // Basic check: Ensure the node has non-empty text content after trimming whitespace.
                if (node.innerText && node.innerText.trim().length > 0) {
                    // Heuristic: Avoid text primarily within a link (likely an author tag or similar).
                    let parent = node.parentElement;
                    let isInsideLink = false;
                    while (parent && parent !== element) { // Traverse up towards the comment root.
                        if (parent.tagName === 'A') {
                            isInsideLink = true; // Found an ancestor 'A' tag.
                            break;
                        }
                        parent = parent.parentElement;
                    }

                    // Relax the link check slightly - a reply might *start* with a link (tag).
                    // Prioritize the longest text block found, assuming it's the main comment body.
                    const currentText = node.innerText.trim();
                    if (!isInsideLink && (!bestText || currentText.length > bestText.length)) {
                        bestText = currentText;
                        bestNode = node; // Remember the node containing this text.
                    }
                    // Handle case where it *might* be inside a link but is still the best candidate so far.
                    // This is less ideal but provides a fallback if the main text is wrapped unexpectedly.
                    else if (isInsideLink && !bestText) {
                        // Tentatively accept text inside a link if nothing else has been found yet.
                        // A later step might clean up leading tags if this is a reply.
                         bestText = currentText;
                         bestNode = node;
                    }
                    // If current text is longer than existing best text *even if inside a link*, update.
                    // This assumes longer text inside a link is more likely the comment than a short tag.
                    else if (isInsideLink && bestText && currentText.length > bestText.length) {
                        bestText = currentText;
                        bestNode = node;
                    }
                }
            });
        }

        // Fallback: If the primary strategy (div[dir=auto]) didn't find text, check direct child SPANs.
        if (!bestText) {
             const children = Array.from(element.children); // Get direct children of the comment element.
             for (let child of children) {
                 // Check if the child is a SPAN, has text, and doesn't contain a link itself (heuristic to avoid author/timestamp spans).
                 if(child.tagName === 'SPAN' && child.innerText && child.innerText.trim().length > 0 && !child.querySelector('a[role="link"]')) {
                    const spanText = child.innerText.trim();
                     // Keep the longest text found among suitable SPANs.
                     if (!bestText || spanText.length > bestText.length) {
                         bestText = spanText;
                         bestNode = child; // Remember the span node.
                     }
                 }
             }
        }

        // Return the best text found (or null) and the node it originated from.
        // The node is useful later for tasks like removing leading tags from replies.
        return { text: bestText, node: bestNode };
    }


    // --- FUNCTION to extract attribute safely ---
    /**
     * Safely gets an attribute value from the first element matching a selector within a parent.
     * @param {Element} element - The parent element to search within.
     * @param {string} selector - The CSS selector for the target element.
     * @param {string} attribute - The name of the attribute to retrieve.
     * @returns {string|null} The attribute value or null if not found.
     */
     function safeGetAttribute(element, selector, attribute) {
        const el = element.querySelector(selector); // Find the element.
        return el ? el.getAttribute(attribute) : null; // Return attribute value or null.
    }

    // --- FUNCTION to extract reaction count ---
    /**
     * Extracts the reaction count from the reaction button's aria-label.
     * @param {Element} element - The comment's root DOM element.
     * @returns {number} The reaction count, or 0 if not found/parsed.
     */
    function getReactionCount(element) {
        const reactionButton = element.querySelector(reactionSelector); // Find the reaction button.
        if (reactionButton) {
            const label = reactionButton.getAttribute('aria-label') || ''; // Get its aria-label.
            const match = label.match(/^(\d+)/); // Use regex to find leading digits (the count).
            if (match && match[1]) {
                return parseInt(match[1], 10); // Parse the digits into an integer.
            }
        }
        return 0; // Default to 0 if no button, label, or number found.
    }

    // --- FUNCTION to extract comment ID (More Robust) ---
    /**
     * Extracts the unique Facebook comment ID (comment_id or reply_comment_id).
     * @param {Element} element - The comment's root DOM element.
     * @returns {string|null} The comment ID or null if not found.
     */
    function getCommentId(element) {
        if (!element) return null; // Early exit if element is null.
        // Find the timestamp link, which usually contains the ID in its href.
        const timestampLinkEl = element.querySelector(timestampSelector);
        if (timestampLinkEl) {
            const timestampLink = timestampLinkEl.getAttribute('href'); // Get the href attribute.
            if (timestampLink) {
                try {
                    // 1. Attempt standard URL parsing (most reliable method).
                    const url = new URL(timestampLink, window.location.origin); // Provide base URL context.
                    const urlParams = url.searchParams; // Get URL parameters.
                    // Look for 'comment_id' or 'reply_comment_id'.
                    let id = urlParams.get("comment_id") || urlParams.get("reply_comment_id");
                    if (id) return id; // Return the ID if found via URL parameters.

                    // 2. Fallback: Use regex on the href string if URL params didn't contain the ID.
                    // This handles cases where the ID might be embedded differently.
                    const idMatch = timestampLink.match(/(?:comment_id|reply_comment_id)=([^&]+)/);
                    if (idMatch && idMatch[1]) return idMatch[1]; // Return ID found via regex.

                } catch (e) {
                    // Log errors during URL parsing but still attempt the regex fallback.
                    console.warn("URL parsing failed for ID, trying regex fallback:", timestampLink, e);
                    // Repeat regex attempt in case of parsing error.
                    const idMatch = timestampLink.match(/(?:comment_id|reply_comment_id)=([^&]+)/);
                    if (idMatch && idMatch[1]) return idMatch[1];
                }
            }
        }
        // Log a warning if no ID could be extracted using any method.
        console.warn("Failed to extract comment ID for element:", element);
        return null; // Return null if ID extraction failed.
    }

    // --- FUNCTION to determine comment type ---
    /**
     * Determines if the comment is an initial comment or a reply based on its aria-label.
     * @param {Element} element - The comment's root DOM element.
     * @returns {'initial' | 'reply' | 'unknown'} The comment type.
     */
    function getCommentType(element) {
        // Relies on the format "Reply by ..." or "Comment by ..." in the aria-label.
        const label = element.getAttribute('aria-label') || '';
        if (label.startsWith('Reply by')) {
            return 'reply';
        } else if (label.startsWith('Comment by')) {
            return 'initial';
        }
        // Return 'unknown' and log a warning if the label doesn't match expected patterns.
        console.warn("Could not determine comment type from aria-label:", label, element);
        return 'unknown';
    }

    // --- NEW FUNCTION to extract author name from an article's aria-label ---
    /**
     * Extracts the author's name from the comment article's aria-label.
     * Primarily used for matching replies to potential parent comments.
     * @param {Element} element - The comment's root DOM element.
     * @returns {string|null} The extracted author name or null if parsing fails.
     */
    function getAuthorNameFromArticleLabel(element) {
        if (!element) return null;
        const label = element.getAttribute('aria-label') || '';
        // Regex attempts to capture text after "Comment by " or "Reply by "
        // up to common terminators like " to " (for replies) or time indicators.
        const commentMatch = label.match(/^(?:Comment|Reply) by (.*?)(?: to | \d+h| \d+m| \d+s| \d+d| \d+w| yesterday| just now)/i);
        if (commentMatch && commentMatch[1]) {
            return commentMatch[1].trim(); // Return the captured name (group 1).
        }
        console.warn("Could not extract author name from article aria-label:", label);
        return null; // Return null if regex doesn't match.
    }

    // --- NEW FUNCTION to extract target author from a reply's aria-label ---
    /**
     * Extracts the name of the author being replied to from a reply's aria-label.
     * Helps identify the correct parent comment. Example: "Reply by Jane to John Doe" -> "John Doe"
     * @param {string} label - The full aria-label of the reply article.
     * @returns {string|null} The target author name or null if not found/parsed.
     */
    function getTargetAuthorFromReplyLabel(label) {
        if (!label) return null;
        // Regex looks for text after " to " or "responding to ", up to possessive "'s" or end of string.
        const match = label.match(/(?:\s+to|responding to)\s+(.*?)(?:'s|$)/i);
        if (match && match[1]) {
            return match[1].trim(); // Return the captured target name (group 1).
        }
        // Don't warn here as not all replies might have this pattern consistently.
        // console.warn("Could not extract target author from reply aria-label:", label);
        return null;
    }

    // --- FIND and PROCESS comments ---
    const commentElements = document.querySelectorAll(commentSelector);
    console.log(`Found ${commentElements.length} potential comment elements using selector: ${commentSelector}`);

    let extractedCount = 0;
    commentElements.forEach((commentEl, index) => {
        // Removed author extraction
        // const authorElement = commentEl.querySelector(authorSelector);
        // const authorName = authorElement ? authorElement.innerText.trim() : null;

        // --- Extract Comment Text using safeGetText ---
        let { text: commentText, node: textNode } = safeGetText(commentEl); // Get text and node

        // --- Determine Comment Type and Extract ID ---
        const commentType = getCommentType(commentEl);
        const commentId = getCommentId(commentEl);

        // --- Find Parent Comment ID (if it's a reply) ---
        let parentCommentId = null;
        if (commentType === 'reply') {
            console.log(`[Debug] Attempting to find parent for reply ID: ${commentId}`, commentEl);

            // 1. Find the reply article element itself
            const selfArticle = commentEl.closest(commentSelector);
            console.log('[Debug] Reply article element (selfArticle):', selfArticle);

            const replyLabel = selfArticle ? selfArticle.getAttribute('aria-label') : '';
            const targetAuthorName = getTargetAuthorFromReplyLabel(replyLabel);
            console.log(`[Debug] Extracted target author from label: "${targetAuthorName}"`);

            if (selfArticle) {
                let currentElement = selfArticle;
                let foundParent = false;
                let fallbackParentId = null;

                // 2. Traverse upwards, checking the immediate previous sibling at each level
                while (currentElement.parentElement && !foundParent) {
                    const parentOfCurrent = currentElement.parentElement;
                    console.log('[Debug] Current level parent:', parentOfCurrent);

                    const prevSibling = currentElement.previousElementSibling;
                    console.log('[Debug] Checking direct previous sibling:', prevSibling);

                    if (prevSibling) {
                        // Find all potential parent articles within or as the previous sibling, check deepest first
                        const candidateArticles = [
                            ...(prevSibling.matches(commentSelector) ? [prevSibling] : []),
                            ...Array.from(prevSibling.querySelectorAll(commentSelector))
                        ].reverse(); 

                        console.log(`[Debug] Found ${candidateArticles.length} potential parent articles in/as previous sibling.`);

                        for (const candidateEl of candidateArticles) {
                            const candidateAuthor = getAuthorNameFromArticleLabel(candidateEl);
                            const candidateId = getCommentId(candidateEl);
                            console.log(`[Debug] Checking candidate: Author="${candidateAuthor}", ID="${candidateId}"`);

                            if (!candidateId) {
                                console.warn("[Debug] Skipping candidate with no ID.");
                                continue;
                            }

                            // Store the first valid ID found as fallback
                            if (!fallbackParentId) {
                                fallbackParentId = candidateId;
                                console.log(`[Debug] Setting fallback parent ID to: ${fallbackParentId}`);
                            }

                            // Try matching via label first
                            if (targetAuthorName && candidateAuthor && candidateAuthor.toLowerCase() === targetAuthorName.toLowerCase()) {
                                console.log(`[Debug] Author match found! ("${candidateAuthor}" vs "${targetAuthorName}")`);
                                parentCommentId = candidateId;
                                foundParent = true; // Set main found flag
                                break; // Break from candidateArticles loop
                            } else {
                                console.log(`[Debug] Author mismatch or missing data (Target: "${targetAuthorName}", Candidate: "${candidateAuthor}")`);
                            }
                        }

                        if(foundParent) break; // Exit upward traversal if match found
                    }

                    // If no match yet, move up
                    if (!foundParent) {
                        console.log('[Debug] Parent not found via label/fallback at this level. Moving up...');
                        currentElement = parentOfCurrent; // Move up
                    }
                } // End upward traversal loop

                // If label matching didn't find a parent, but we found a fallback, use it.
                if (!foundParent && fallbackParentId) {
                    console.log(`[Debug] Label matching failed or was not possible. Using fallback parent ID: ${fallbackParentId}`);
                    parentCommentId = fallbackParentId;
                    foundParent = true; // Consider it found for logging purposes
                } else if (foundParent) {
                    console.log(`[Debug] Successfully found parent via label matching: ${parentCommentId}`);
                }
            }

            // 5. Log warning if no parent was found after traversal
            if (!parentCommentId) {
                 console.warn(`[Debug] Could not find DIRECT parent article for reply ID ${commentId || '(unknown)'} after traversing up and checking siblings/descendants.`);
            }
        }

        // --- Attempt to remove leading tagged name from replies ---
        if (commentType === 'reply' && commentText && textNode) {
            const firstChild = textNode.firstElementChild;
            if (firstChild && firstChild.tagName === 'A') {
                const taggedName = firstChild.innerText.trim();
                if (taggedName && commentText.startsWith(taggedName)) {
                    // Remove the name and potentially one following space
                    commentText = commentText.substring(taggedName.length).trimStart();
                    console.log(`Removed leading tag "${taggedName}" from reply ID ${commentId}`);
                }
            }
        }

        // --- REVISED Timestamp Text Extraction (from innerHTML) ---
        let timestampText = "Unknown Timestamp";
        const debugCommentHTML = commentEl.innerHTML; // Need innerHTML just for the text
        // Ensure regex escaping is correct for edit tool: \ needs to become \\
        const timestampRegex = /<a\s+[^>]*href=[^>]*comment_id=[^>]*>([^<]+?)<\/a>/i;
        const match = debugCommentHTML.match(timestampRegex);
        if (match && match[1]) {
            timestampText = match[1].trim();
        } else {
             // Attempt to find reply timestamp text as fallback
             const replyTimestampRegex = /<a\s+[^>]*href=[^>]*reply_comment_id=[^>]*>([^<]+?)<\/a>/i;
             const replyMatch = debugCommentHTML.match(replyTimestampRegex);
             if (replyMatch && replyMatch[1]) {
                 timestampText = replyMatch[1].trim();
             } else {
                 console.warn(`Comment ${index + 1} (ID: ${commentId}): Regex failed to find timestamp text in debug HTML.`);
             }
        }

        // --- Add comment data to list ---
        if (commentText) {
            comments.push({
                id: commentId || `missing_id_${index}`,
                parent_id: parentCommentId, // Will be null for initial comments
                text: commentText,
                timestamp_text: timestampText,
                reaction_count: getReactionCount(commentEl),
                comment_type: commentType
            });
            extractedCount++;
            // Updated log message
            console.log(`Added comment ${index + 1}: Type: ${commentType}. ParentID: ${parentCommentId}. Reactions: ${getReactionCount(commentEl)}. ID: ${commentId}.`);
        } else {
            console.warn(`Comment ${index + 1} (ID: ${commentId}): Could not extract comment text.`);
        }
    });

    // --- OUTPUT ---
    console.log(`Successfully extracted text from ${extractedCount} out of ${commentElements.length} potential elements.`);
    if (comments.length > 0) {
        console.log(`Total comments added to JSON: ${comments.length}`);
        console.log("Copy the JSON data below:");
        console.log(JSON.stringify(comments, null, 2));
    } else {
        console.log("No comments extracted. Selectors might need updating, or comments weren't loaded.");
    }
})(); 