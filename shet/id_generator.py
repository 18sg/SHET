

class IdGeneratorMixin(object):
	
	_last_id = 0

	def get_id(self):
		self._last_id += 1
		return self._last_id
