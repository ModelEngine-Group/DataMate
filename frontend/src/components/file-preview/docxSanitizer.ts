const ALLOWED_DOCX_TAGS = new Set([
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'p', 'br', 'hr', 'ul', 'ol', 'li',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'strong', 'em', 'b', 'i', 'u', 's',
  'a', 'img', 'sup', 'sub', 'pre', 'code', 'blockquote', 'span', 'div',
]);

const DROP_WITH_CONTENT_TAGS = new Set([
  'base', 'button', 'embed', 'form', 'iframe', 'input', 'link', 'math',
  'meta', 'object', 'script', 'select', 'style', 'svg', 'textarea',
]);

const VOID_TAGS = new Set(['br', 'hr', 'img']);

const SAFE_LINK_PROTOCOLS = new Set(['http:', 'https:', 'mailto:', 'tel:']);
const SAFE_IMAGE_DATA_URI_PATTERN = /^data:image\/(?:png|jpe?g|gif|webp|bmp);base64,[a-z0-9+/=\s]+$/i;
const SAFE_ANCHOR_PATTERN = /^#[a-z0-9_.:-]+$/i;
const SAFE_DIMENSION_PATTERN = /^(?:[1-9]\d{0,3}|10000)$/;
const SAFE_SPAN_PATTERN = /^(?:[1-9]|[1-9]\d|100)$/;

function isSafeDocxLink(rawHref: string | null): boolean {
  if (!rawHref) {
    return false;
  }

  const href = rawHref.trim();
  if (SAFE_ANCHOR_PATTERN.test(href)) {
    return true;
  }

  try {
    const parsed = new URL(href);
    return SAFE_LINK_PROTOCOLS.has(parsed.protocol);
  } catch {
    return false;
  }
}

function isSafeDocxImageSource(rawSrc: string | null): boolean {
  return Boolean(rawSrc && SAFE_IMAGE_DATA_URI_PATTERN.test(rawSrc.trim()));
}

function setPlainTextAttribute(target: HTMLElement, source: Element, attrName: string): void {
  const value = source.getAttribute(attrName);
  if (value) {
    target.setAttribute(attrName, value);
  }
}

function setNumericAttribute(
  target: HTMLElement,
  source: Element,
  attrName: string,
  pattern: RegExp,
): void {
  const value = source.getAttribute(attrName)?.trim();
  if (value && pattern.test(value)) {
    target.setAttribute(attrName, value);
  }
}

function copySafeAttributes(target: HTMLElement, source: Element, tagName: string): boolean {
  setPlainTextAttribute(target, source, 'title');

  if (tagName === 'a') {
    const href = source.getAttribute('href');
    if (isSafeDocxLink(href)) {
      target.setAttribute('href', href!.trim());
    }
  }

  if (tagName === 'img') {
    const src = source.getAttribute('src');
    if (!isSafeDocxImageSource(src)) {
      return false;
    }
    target.setAttribute('src', src!.trim());
    setPlainTextAttribute(target, source, 'alt');
    setNumericAttribute(target, source, 'width', SAFE_DIMENSION_PATTERN);
    setNumericAttribute(target, source, 'height', SAFE_DIMENSION_PATTERN);
  }

  if (tagName === 'td' || tagName === 'th') {
    setNumericAttribute(target, source, 'colspan', SAFE_SPAN_PATTERN);
    setNumericAttribute(target, source, 'rowspan', SAFE_SPAN_PATTERN);
  }

  return true;
}

function sanitizeNode(node: Node): Node[] {
  if (node.nodeType === Node.TEXT_NODE) {
    return [document.createTextNode(node.textContent ?? '')];
  }

  if (node.nodeType !== Node.ELEMENT_NODE) {
    return [];
  }

  const element = node as Element;
  const tagName = element.tagName.toLowerCase();
  if (DROP_WITH_CONTENT_TAGS.has(tagName)) {
    return [];
  }

  const sanitizedChildren = Array.from(element.childNodes).flatMap(sanitizeNode);
  if (!ALLOWED_DOCX_TAGS.has(tagName)) {
    return sanitizedChildren;
  }

  const sanitizedElement = document.createElement(tagName);
  if (!copySafeAttributes(sanitizedElement, element, tagName)) {
    return [];
  }

  if (!VOID_TAGS.has(tagName)) {
    sanitizedElement.append(...sanitizedChildren);
  }

  return [sanitizedElement];
}

export function sanitizeDocxHtml(html: string): string {
  const source = document.createElement('template');
  source.innerHTML = html;

  const container = document.createElement('div');
  container.append(...Array.from(source.content.childNodes).flatMap(sanitizeNode));
  return container.innerHTML;
}
