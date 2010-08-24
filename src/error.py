def serialize_error(error):
	if isinstance(error, Exception):
		return (error.__class__.__name__,
		         error.args)
	elif isinstance(error, (list, tuple)):
		if len(error) == 2 and isinstance(error[1], (list, tuple)):
			return error
		else:
			return ["UnknownError",
			        error]
	elif hasattr(error, "value"):
		return serialize_error(error.value)
	else:
		return ["UnknownError", [str(error)]]

class ShetException(Exception):
	pass
