// Execute the shipped inline script against a small DOM double. Browser QA is separate.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];

class Element {
    constructor(text = '', dataset = {}) {
        this.textContent = text;
        this.dataset = dataset;
        this.hidden = false;
        this.events = {};
        this.attributes = {};
        this.children = [];
        this.value = '';
        this.classList = {toggle() {}};
    }
    addEventListener(name, callback) { this.events[name] = callback; }
    setAttribute(name, value) { this.attributes[name] = value; }
    removeAttribute(name) { delete this.attributes[name]; }
    get innerText() { return this.hidden ? '' : this.textContent; }
    append(row) { this.children.push(row); }
    scrollIntoView() {}
    fire(name) { this.events[name](); }
}

function table(id, rows, pageSize) {
    const result = new Element('', pageSize ? {pageSize: String(pageSize)} : {});
    result.id = id;
    result.rows = rows.map(([sample, number, status]) => {
        const row = new Element(`${sample} ${number} ${status}`, {qcStatus: status, sampleId: sample});
        row.children = [new Element(sample), new Element(String(number)), new Element(status)];
        return row;
    });
    result.body = {querySelectorAll: () => result.rows, appendChild(row) {
        result.rows.splice(result.rows.indexOf(row), 1);
        result.rows.push(row);
    }};
    result.headers = ['string', 'numeric', 'status'].map(type => {
        const header = new Element('', {type});
        header.button = new Element();
        header.querySelector = () => header.button;
        header.closest = () => result;
        return header;
    });
    result.headers.forEach(header => { header.parentElement = {children: result.headers}; });
    result.querySelectorAll = selector => selector === 'thead th' ? result.headers : result.rows;
    result.querySelector = () => result.body;
    return result;
}

for (const size of [4, 80]) {
    const statuses = ['FAIL', 'WARN', 'NOT_EVALUATED', 'PASS'];
    const review = table('sample-review-table', Array.from({length:size}, (_, i) => [`sample-${i}`, size-i, statuses[i%4]]), size > 25 ? 25 : 0);
    const full = table('full-detail-table', [['zeta',30,'PASS'], ['alpha',2,'WARN'], ['beta',10,'FAIL']], 0);
    const tables = [review, full];
    const filters = tables.map(item => { const filter = new Element('', {target:item.id}); filter.id = `${item.id}-filter`; return filter; });
    const empties = tables.map(item => new Element('', {target:item.id}));
    const summary = new Element();
    const tabs = new Element('', {defaultFilter:'NEEDS_REVIEW'});
    const buttons = ['ALL', 'FAIL', 'WARN', 'PASS', 'NOT_EVALUATED', 'NEEDS_REVIEW'].map(status => {
        const button = new Element('', {statusFilter:status});
        button.closest = () => tabs;
        return button;
    });
    const controls = new Element('', {target:review.id});
    const previous = new Element();
    const next = new Element();
    const pageStatus = new Element();
    controls.querySelector = selector => ({'.table-page-prev':previous, '.table-page-next':next, '.table-page-status':pageStatus})[selector];
    const nodes = Object.fromEntries([...tables, ...filters].map(item => [item.id, item]));
    nodes['review-filter-summary'] = summary;
    nodes['sample-review'] = new Element();
    const document = {
        body: new Element(),
        createElement: () => new Element(),
        getElementById: id => nodes[id] || null,
        querySelector(selector) {
            if (selector === '.status-tabs') return tabs;
            if (selector === '.table-pagination[data-target="sample-review-table"]') return size > 25 ? controls : null;
            if (selector.startsWith('.table-empty')) return empties.find(item => selector.includes(`"${item.dataset.target}"`));
            return null;
        },
        querySelectorAll(selector) {
            return ({
                'table.js-sort-filter thead th': tables.flatMap(item => item.headers),
                '.table-filter': filters,
                '.table-pagination': size > 25 ? [controls] : [],
                '[data-status-filter]':buttons,
                '.sample-review-row': review.rows,
            })[selector] || [];
        },
    };
    const printDetails = [{open:true}, {open:false}];
    const originalQuery = document.querySelectorAll;
    document.querySelectorAll = selector => selector === 'details' ? printDetails : originalQuery(selector);
    const windowEvents = {};
    vm.runInNewContext(script, {document, window:{addEventListener(name, callback) {windowEvents[name] = callback;}}});
    windowEvents.beforeprint();
    assert.ok(printDetails.every(detail => detail.open));
    windowEvents.afterprint();
    assert.deepEqual(printDetails.map(detail => detail.open), [true, false]);
    const shown = () => review.rows.filter(row => !row.hidden);
    assert.ok(shown().every(row => row.dataset.qcStatus !== 'PASS'));
    buttons.find(button => button.dataset.statusFilter === 'PASS').fire('click');
    assert.equal(shown().length, Math.min(size/4, 25));
    assert.ok(shown().every(row => row.dataset.qcStatus === 'PASS'));
    filters[0].value = 'no match';
    filters[0].fire('input');
    assert.equal(shown().length, 0);
    assert.equal(empties[0].hidden, false);
    assert.match(summary.textContent, /Showing 0 samples with PASS status matching the text filter/);
    filters[0].value = 'sample-3';
    filters[0].fire('input');
    assert.ok(shown().some(row => row.dataset.sampleId === 'sample-3'), 'search must find previously hidden rows');
    filters[0].value = '';
    filters[0].fire('input');
    buttons.find(button => button.dataset.statusFilter === 'ALL').fire('click');
    // Every table uses its own column index, including the second table.
    full.headers[1].button.fire('click');
    assert.deepEqual(full.rows.map(row => Number(row.children[1].textContent)), [2,10,30]);
    assert.equal(full.headers[1].attributes['aria-sort'], 'ascending');
    full.headers[0].button.fire('click');
    assert.equal(full.headers[1].attributes['aria-sort'], undefined);
    assert.equal(full.headers[0].attributes['aria-sort'], 'ascending');
    if (size > 25) {
        assert.equal(shown().length, 25);
        next.fire('click');
        assert.equal(pageStatus.textContent, '26-50 of 80');
        filters[0].value = 'sample-79';
        filters[0].fire('input');
        assert.equal(shown().length, 1);
        assert.equal(pageStatus.textContent, '1-1 of 1');
        assert.equal(next.disabled, true);
        assert.equal(previous.disabled, true);
    }
}
console.log('Small and paginated reports: combined filters, empty state, page reset, second-table sorting and aria-sort passed.');
