/**
 * SIC-JS v3.0 Web Components
 * ===========================
 * Three custom elements for rendering SIC-JS state in HTML.
 * 
 * Usage:
 *   <sic-task id="A-1" status="in_progress">
 *     <span slot="title">My Task</span>
 *     <span slot="action">Working on it</span>
 *   </sic-task>
 *
 *   <sic-state field="current_action">Thinking...</sic-state>
 *
 *   <sic-entity name="德德" model="Claude Sonnet 4.6"></sic-entity>
 *
 * License: MIT
 */

// === <sic-task> ===
class SicTaskElement extends HTMLElement {
  static get observedAttributes() {
    return ['status', 'data-sic-id', 'data-sic-status'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          border: 2px solid var(--sic-border, #e0e0e0);
          border-radius: 8px;
          padding: 12px 16px;
          margin: 8px 0;
          font-family: system-ui, -apple-system, sans-serif;
          transition: border-color 0.3s, background-color 0.3s;
        }
        :host([status="pending"]) {
          border-color: #ffc107;
          background-color: #fff8e1;
        }
        :host([status="in_progress"]) {
          border-color: #2196f3;
          background-color: #e3f2fd;
        }
        :host([status="completed"]) {
          border-color: #4caf50;
          background-color: #e8f5e9;
        }
        :host([status="dismissed"]) {
          border-color: #9e9e9e;
          background-color: #f5f5f5;
          opacity: 0.7;
        }
        :host([status="archived"]) {
          border-color: #607d8b;
          background-color: #eceff1;
          opacity: 0.5;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .task-id {
          font-weight: 700;
          font-size: 0.85em;
          color: #555;
          font-family: monospace;
        }
        .status-badge {
          font-size: 0.75em;
          padding: 2px 8px;
          border-radius: 12px;
          background: currentColor;
          color: white;
        }
        .content {
          font-size: 0.95em;
        }
      </style>
      <div class="header">
        <span class="task-id"></span>
        <span class="status-badge"></span>
      </div>
      <div class="content">
        <slot name="title"></slot>
        <slot name="action"></slot>
      </div>
    `;
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback() {
    this._render();
  }

  _render() {
    const id = this.getAttribute('data-sic-id') || this.id || '?';
    const status = this.getAttribute('status') || this.getAttribute('data-sic-status') || 'pending';
    this.setAttribute('status', status);
    
    const idEl = this.shadowRoot.querySelector('.task-id');
    const badgeEl = this.shadowRoot.querySelector('.status-badge');
    if (idEl) idEl.textContent = id;
    if (badgeEl) badgeEl.textContent = status;
  }

  // Public API: update from SIC-JS record
  updateFromRecord(record) {
    if (record.task) {
      this.setAttribute('data-sic-id', record.task.id);
      this.setAttribute('status', record.task.status);
      if (record.task.title) {
        const titleSlot = this.querySelector('[slot="title"]');
        if (titleSlot) titleSlot.textContent = record.task.title;
      }
    }
    if (record.state && record.state.current_action) {
      const actionSlot = this.querySelector('[slot="action"]');
      if (actionSlot) actionSlot.textContent = record.state.current_action;
    }
  }
}

// === <sic-state> ===
class SicStateElement extends HTMLElement {
  static get observedAttributes() {
    return ['field', 'data-sic-value'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: inline-block;
          font-family: monospace;
          padding: 2px 6px;
          border-radius: 4px;
          background: #f0f4f8;
          border: 1px solid #d0d7de;
          transition: background-color 0.2s;
        }
        :host([data-sic-value=""]),
        :host(:not([data-sic-value])) {
          background: #fff3cd;
          border-color: #ffc107;
        }
        .field-name {
          font-size: 0.75em;
          color: #666;
        }
        .field-value {
          font-weight: 500;
        }
      </style>
      <span class="field-name"></span>
      <span class="field-value"><slot></slot></span>
    `;
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback() {
    this._render();
  }

  _render() {
    const field = this.getAttribute('field') || '';
    const nameEl = this.shadowRoot.querySelector('.field-name');
    if (nameEl && field) nameEl.textContent = field + ': ';
  }

  updateValue(value) {
    this.setAttribute('data-sic-value', value || '');
    this.textContent = value || '[null]';
  }
}

// === <sic-entity> ===
class SicEntityElement extends HTMLElement {
  static get observedAttributes() {
    return ['name', 'model'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 16px;
          background: #e8eaf6;
          border: 1px solid #c5cae9;
          font-family: system-ui, sans-serif;
          font-size: 0.9em;
        }
        .avatar {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #3f51b5;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 0.7em;
          font-weight: 700;
        }
        .name { font-weight: 600; }
        .model { font-size: 0.8em; color: #666; }
      </style>
      <span class="avatar"></span>
      <span class="name"></span>
      <span class="model"></span>
    `;
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback() {
    this._render();
  }

  _render() {
    const name = this.getAttribute('name') || '?';
    const model = this.getAttribute('model') || '';
    
    const avatarEl = this.shadowRoot.querySelector('.avatar');
    const nameEl = this.shadowRoot.querySelector('.name');
    const modelEl = this.shadowRoot.querySelector('.model');
    
    if (avatarEl) avatarEl.textContent = name.charAt(0);
    if (nameEl) nameEl.textContent = name;
    if (modelEl) modelEl.textContent = model ? `(${model})` : '';
  }
}

// Register all components
customElements.define('sic-task', SicTaskElement);
customElements.define('sic-state', SicStateElement);
customElements.define('sic-entity', SicEntityElement);

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SicTaskElement, SicStateElement, SicEntityElement };
}
