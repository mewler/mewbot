

@simplecommand
async def becute(logger, context) -> bool:
	await context.reply_all("meow :3")

	return True

@paramcommand(0, 1)
async def dothing(logger, context, *args: str) -> bool:
	// As above


class StaticText(SimpleCommand):
	_text: str

	async def execute(logger, context) -> bool:
		await context.reply_all(self.text)
		return True

	@property
	def text(self) -> str:
		self._text = text

	@text.setter
	def text(self, value: str):
		self._text = value
