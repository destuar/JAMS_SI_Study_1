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
    function safeGetText(element) {
        // Find ALL divs with dir="auto" within the current comment element
        const potentialTextNodes = element.querySelectorAll(potentialTextSelector);
        let bestText = null;
        let bestNode = null; // Keep track of the node containing the best text

        if (potentialTextNodes.length > 0) {
            // Filter and find the most likely candidate
            potentialTextNodes.forEach(node => {
                // Basic check: Must have some text content
                if (node.innerText && node.innerText.trim().length > 0) {
                    // Avoid text that is clearly inside a link (likely author/tag)
                    let parent = node.parentElement;
                    let isInsideLink = false;
                    while (parent && parent !== element) {
                        if (parent.tagName === 'A') {
                            isInsideLink = true;
                            break;
                        }
                        parent = parent.parentElement;
                    }

                    // We relax the link check slightly; we will handle leading links later if it's a reply
                    // The main goal here is finding the most substantial text block
                    const currentText = node.innerText.trim();
                    if (!bestText || currentText.length > bestText.length) {
                        bestText = currentText;
                        bestNode = node; // Store the node
                    }
                }
            });
        }

        // Fallback: If no div[dir=auto] worked, check direct child spans
        if (!bestText) {
             const children = Array.from(element.children);
             for (let child of children) {
                 // Ensure it's a SPAN, has text, and isn't itself a link container
                 if(child.tagName === 'SPAN' && child.innerText && child.innerText.trim().length > 0 && !child.querySelector('a[role="link"]')) {
                    const spanText = child.innerText.trim();
                     if (!bestText || spanText.length > bestText.length) {
                         bestText = spanText;
                         bestNode = child; // Store the node
                     }
                 }
             }
        }

        // Return both the text and the node it came from
        return { text: bestText, node: bestNode };
    }


    // --- FUNCTION to extract attribute safely ---
     function safeGetAttribute(element, selector, attribute) {
        const el = element.querySelector(selector);
        return el ? el.getAttribute(attribute) : null;
    }

    // --- FUNCTION to extract reaction count ---
    function getReactionCount(element) {
        const reactionButton = element.querySelector(reactionSelector);
        if (reactionButton) {
            const label = reactionButton.getAttribute('aria-label') || '';
            const match = label.match(/^(\d+)/); // Match digits at the beginning
            if (match && match[1]) {
                return parseInt(match[1], 10);
            }
        }
        return 0; // Default to 0 if not found or number not parsed
    }

    // --- FUNCTION to extract comment ID (More Robust) ---
    function getCommentId(element) {
        if (!element) return null;
        const timestampLinkEl = element.querySelector(timestampSelector); // Use the specific selector
        if (timestampLinkEl) {
            const timestampLink = timestampLinkEl.getAttribute('href');
            if (timestampLink) {
                try {
                    // Attempt standard URL parsing first
                    const url = new URL(timestampLink, window.location.origin);
                    const urlParams = url.searchParams;
                    let id = urlParams.get("comment_id") || urlParams.get("reply_comment_id");
                    if (id) return id;

                    // Fallback: Regex on the href attribute if params not found
                    const idMatch = timestampLink.match(/(?:comment_id|reply_comment_id)=([^&]+)/);
                    if (idMatch && idMatch[1]) return idMatch[1];

                } catch (e) {
                    // Log error if URL parsing fails, but still try regex as fallback
                    console.warn("URL parsing failed for ID, trying regex fallback:", timestampLink, e);
                    const idMatch = timestampLink.match(/(?:comment_id|reply_comment_id)=([^&]+)/);
                    if (idMatch && idMatch[1]) return idMatch[1];
                }
            }
        }
        console.warn("Failed to extract comment ID for element:", element);
        return null; // No ID found through reliable methods
    }

    // --- FUNCTION to determine comment type ---
    function getCommentType(element) {
        const label = element.getAttribute('aria-label') || '';
        if (label.startsWith('Reply by')) {
            return 'reply';
        } else if (label.startsWith('Comment by')) {
            return 'initial';
        }
        return 'unknown'; // Fallback if label doesn't match expected patterns
    }

    // --- NEW FUNCTION to extract author name from an article's aria-label ---    
    function getAuthorNameFromArticleLabel(element) {
        if (!element) return null;
        const label = element.getAttribute('aria-label') || '';
        const commentMatch = label.match(/^(?:Comment|Reply) by (.*?)(?: to| \d+)/i);
        if (commentMatch && commentMatch[1]) {
            return commentMatch[1].trim();
        }
        console.warn("Could not extract author name from article aria-label:", label);
        return null; // Fallback if label doesn't match
    }

    // --- NEW FUNCTION to extract target author from a reply's aria-label ---
    function getTargetAuthorFromReplyLabel(label) {
        if (!label) return null;
        // Regex to find name after "to" or "responding to" and before "'s" or end of string (case-insensitive)
        const match = label.match(/(?:\s+to|responding to)\s+(.*?)(?:'s|$)/i);
        if (match && match[1]) {
            return match[1].trim();
        }
        console.warn("Could not extract target author from reply aria-label:", label);
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