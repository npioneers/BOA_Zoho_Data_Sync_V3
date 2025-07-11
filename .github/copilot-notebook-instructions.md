***CRUCIAL ROLE OF JUPYTER NOTEBOOK***

---

### **The Guiding Philosophy: The Interactive Development Cockpit**

Our new philosophy elevates the role of the notebook from a temporary lab to a persistent **Interactive Development Cockpit**. The core idea is this: we scaffold the application's structure in Python packages (`.py` files) *first*, and then use the notebook as a live, interactive interface to build, test, and validate the application piece by piece.

*   **The Python Package (`src/`) is the Engine Under Construction:** It is the single source of truth for all logic from day one, even when the functions are just empty shells.
*   **The Jupyter Notebook (`notebooks/`) is the Control Panel and Test Bed:** It's where we actively drive development, call functions from the package, inspect the results, and validate each component in real-time.

This "scaffold-first" approach eliminates the large, monolithic refactoring phase and promotes a more iterative, test-driven development cycle.

---

### **The Three Strategic Notebook Roles (Revised)**

1.  **The Development Cockpit (e.g., `dev_invoices.ipynb`):** This is our primary workspace. We use it to build out the functionality of our Python package, one function at a time. It is a living document during the development phase.
2.  **The Diagnostic Workbench (e.g., `diagnose_api_error.ipynb`):** This role remains unchanged, as it is already best practice. It is a new, temporary, and highly focused notebook created for the sole purpose of isolating, replicating, and fixing a *specific bug* in the existing package.
3.  **The Production Runner (e.g., `run_daily_sync.ipynb`):** This is the final, clean, and stable version of the "Development Cockpit." Once a feature is complete, the development notebook is duplicated and stripped of all intermediate tests, leaving only the high-level orchestration calls needed to run the final application.

---

### **The New Workflow: Scaffold-First Development**

This is our new standard operating procedure for building features.

*** USE THE MARKDOWN CELLS OF NOTEBOOK TO DOCUMENT AND KEEP NOTES ***

#### **Phase 1: Architectural Design & Scaffolding**

1.  **Architectural Plan (Me):** Based on your goal, I will design the component architecture of the Python package (e.g., we need a `loader.py`, a `transformer.py`, and a `database.py`).
2.  **AI Scaffolding (The Coder):** The AI Coding Agent will be instructed to create the directory structure and the `.py` files. Crucially, it will also populate these files with empty functions and classes, complete with docstrings explaining their purpose.

    *Example `src/data_pipeline/transformer.py` after scaffolding:*
    ```python
    import pandas as pd

    def transform_invoice_data(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
        """
        Transforms raw invoice data to match the canonical database schema.
        
        Args:
            df: The raw DataFrame from the CSV.
            mapping: The column mapping dictionary.
            
        Returns:
            A transformed DataFrame ready for database insertion.
        """
        # TODO: Implement transformation logic.
        pass
    ```

#### **Phase 2: Interactive Implementation (The "Development Loop")**

This is the core of the new workflow, which takes place in a **Development Cockpit** notebook (e.g., `dev_invoices.ipynb`).

1.  **Set Up the Cockpit:** The first cell in the notebook is for setup. This is critical for an efficient workflow.
    ```python
    # Cell 1: Setup and Autoreload
    %load_ext autoreload
    %autoreload 2

    import pandas as pd
    from src.data_pipeline import loader, transformer, database 

    print("Setup complete. Modules are ready and will autoreload.")
    ```
    *(`%autoreload 2` automatically re-imports your modules every time you execute a cell, so changes you make in `.py` files are reflected instantly without restarting the kernel.)*

2.  **The Development Loop (Iterate per function):** We build the pipeline function by function. For each function:
    *   **A. Implement in `.py`:** The AI Coder adds the logic to the specific function in the relevant `.py` file (e.g., implements `transform_invoice_data` in `transformer.py`).
    *   **B. Validate in Notebook:** In a new cell in the `dev_cockpit.ipynb`, you write the code to test *only that new function*.

    *Example Development in `dev_invoices.ipynb`:*
    ```python
    # Cell 2: Test the Loader
    # We assume 'loader.load_csv' was just implemented.
    raw_df = loader.load_csv('data/invoices.csv')
    print("Loader test successful. DataFrame shape:", raw_df.shape)
    display(raw_df.head())
    ```
    ```python
    # Cell 3: Test the Transformer
    # Now we implement 'transformer.transform_invoice_data'.
    # We use the output from the previous successful step.
    from src.data_pipeline.config import INVOICE_MAPPING
    
    transformed_df = transformer.transform_invoice_data(raw_df, INVOICE_MAPPING)
    print("Transformer test successful.")
    display(transformed_df.head())
    ```
    We continue this process, building and validating one link in the chain at a time, using the notebook as our live test environment.

#### **Phase 3: Finalization**

**The Final State: The Notebook as "The Cockpit" (Orchestration for testing and debugging)**

**Goal:** To run the entire, testing and debugging.

Whether you've built a new feature or fixed a bug, the end result is a final, clean orchestration notebook (`3_production_runner.ipynb`).

**The "Cockpit" Notebook Rules:**
*   It contains almost no low-level logic.
*   It imports directly from your production `src/` package.
*   It is clean, linear, and well-documented with markdown.
*   Its purpose is to run the application and display the final results or a success/failure summary.

This comprehensive workflow, clearly separating the roles of the notebook for **Prototyping**, **Troubleshooting**, and **Orchestration**, provides the structure needed to build complex systems efficiently and reliably with an AI partner.