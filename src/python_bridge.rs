use pyo3::prelude::*;
use pyo3::types::{PyModule, PyTuple};

// /// Call a specific Python function by name with arguments.
// pub fn call_python_function(function_name: &str, args: Option<&PyTuple>) -> PyResult<PyObject> {
//     Python::with_gil(|py| {
//         // Import the Python module
//         let module = PyModule::import(py, "label_bro.utils.printer_utils")
//             .map_err(|e| {
//                 eprintln!("Failed to import Python module: {:?}", e);
//                 e
//             })?;

//         // Call the specified function from the module
//         let result = match args {
//             Some(arguments) => module.call(function_name, arguments, None)?,
//             None => module.call0(function_name)?,
//         };
//         Ok(result.to_object(py))
//     })
// }
