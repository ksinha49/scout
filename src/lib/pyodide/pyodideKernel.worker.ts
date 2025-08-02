/**
 * | 2025-19-02 | X1BA           | CWE-79            | Improper Neutralization of Input During Web Page Generation - Cross-site Scripting                                                                |
 */
import { loadPyodide, type PyodideInterface } from 'pyodide';

declare global {
	interface Window {
		stdout: string | null;
		stderr: string | null;
		pyodide: PyodideInterface;
		cells: Record<string, CellState>;
		indexURL: string;
	}
}

type CellState = {
	id: string;
	status: 'idle' | 'running' | 'completed' | 'error';
	result: any;
	stdout: string;
	stderr: string;
};

// MOD TAG CWE-79 - Improper Neutralization of Input During Web Page Generation - Cross-site Scripting
function validateId(id:string) {
	if (id === '__proto__' || id === 'constructor' || id === 'prototype') {
		throw new Error('Invalid cell id');
	 }
}
const initializePyodide = async () => {
	// Ensure Pyodide is loaded once and cached in the worker's global scope
	if (!self.pyodide) {
		self.indexURL = '/pyodide/';
		self.stdout = '';
		self.stderr = '';
		self.cells = {};

		self.pyodide = await loadPyodide({
			indexURL: self.indexURL
		});
	}
};

const executeCode = async (id: string, code: string) => {
	if (!self.pyodide) {
		await initializePyodide();
	}
	// MOD TAG CWE-79 - Improper Neutralization of Input During Web Page Generation - Cross-site Scripting
	validateId(id);
	// Update the cell state to "running"
	self.cells[id] = {
		id,
		status: 'running',
		result: null,
		stdout: '',
		stderr: ''
	};

	// Redirect stdout/stderr to stream updates
	self.pyodide.setStdout({
		batched: (msg: string) => {
			self.cells[id].stdout += msg;
			self.postMessage({ type: 'stdout', id, message: msg });
		}
	});
	self.pyodide.setStderr({
		batched: (msg: string) => {
			self.cells[id].stderr += msg;
			self.postMessage({ type: 'stderr', id, message: msg });
		}
	});

	try {
		// Dynamically load required packages based on imports in the Python code
		await self.pyodide.loadPackagesFromImports(code, {
			messageCallback: (msg: string) => {
				self.postMessage({ type: 'stdout', id, package: true, message: `[package] ${msg}` });
			},
			errorCallback: (msg: string) => {
				self.postMessage({ type: 'stderr', id, package: true, message: `[package] ${msg}` });
			}
		});

		// Execute the Python code
		const result = await self.pyodide.runPythonAsync(code);
		// MOD TAG CWE-79 - Improper Neutralization of Input During Web Page Generation - Cross-site Scripting
		validateId(id);
		self.cells[id].result = result;
		self.cells[id].status = 'completed';
	} catch (error:unknown) {
		// MOD TAG CWE-79 - Improper Neutralization of Input During Web Page Generation - Cross-site Scripting
		let errorMessage: string;
		if (error instanceof Error) {
		  errorMessage = error.message;
		} else {
		  errorMessage = String(error);
		}
		validateId(id);
		self.cells[id].status = 'error';
		self.cells[id].stderr += errorMessage;
	} finally {
		// Notify parent thread when execution completes
		self.postMessage({
			type: 'result',
			id,
			state: self.cells[id]
		});
	}
};

// Handle messages from the main thread
self.onmessage = async (event) => {
	const { type, id, code, ...args } = event.data;

	switch (type) {
		case 'initialize':
			await initializePyodide();
			self.postMessage({ type: 'initialized' });
			break;

		case 'execute':
			if (id && code) {
				await executeCode(id, code);
			}
			break;

		case 'getState':
			self.postMessage({
				type: 'kernelState',
				state: self.cells
			});
			break;

		case 'terminate':
			// Explicitly clear the worker for cleanup
			for (const key in self.cells) {
				// MOD TAG CWE-79 - Improper Neutralization of Input During Web Page Generation - Cross-site Scripting
				validateId(key);
				delete self.cells[key];
			}
			self.close();
			break;

		default:
			console.error(`Unknown message type: ${type}`);
	}
};