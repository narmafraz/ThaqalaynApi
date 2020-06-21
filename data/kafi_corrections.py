import os

CORRECTIONS = {
	'c005.xhtml': [
		{
			'before': '<a id="_ftnref13"/><sup>[13]</sup> ',
			'after': ''
		}
	],
	'c072.xhtml': [
		{
			'before': 'Chapater 4',
			'after': 'Chapter 4'
		}
	],
	'c107.xhtml': [
		{
			'before': '<p style="text-align: justify" dir="rtl">&#1576;&#1575;<span style="font-weight: bold; text-decoration: underline">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">&#1576;&#1575;'
		},
		{
			'before': '</span></p>',
			'after': '</p>'
		}
	],
	'c150.xhtml': [
		{
			'before': '<p style="text-align: justify" dir="rtl">&#1576;&#1614;&#1575;<span style="font-weight: bold; text-decoration: underline">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">&#1576;&#1614;&#1575;'
		},
		{
			'before': '</span></p>',
			'after': '</p>'
		}
	],
	'c187.xhtml': [
		{
			'before': '<p style="text-align: justify" dir="rtl">&#1576;&#1575;<span style="font-weight: bold; text-decoration: underline">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">&#1576;&#1575;'
		},
		{
			'before': '</span></p>',
			'after': '</p>'
		}
	], # Volume 2
	'c134.xhtml': [
		{
			'before': 'Chater',
			'after': 'Chapter'
		}
	],
	'c223.xhtml': [
		{
			'before': 'Cahpter',
			'after': 'Chapter'
		}
	],
	'c239.xhtml': [
		{
			'before': '<p style="text-align: justify" dir="rtl">&#1576;&#1614;&#1575;<span style="font-weight: bold; text-decoration: underline">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">&#1576;&#1614;&#1575;'
		},
		{
			'before': '</span></p>',
			'after': '</p>'
		}
	], # Volume 3
	'c018.xhtml': [
		{
			'before': 'Chapater',
			'after': 'Chapter'
		}
	],
	'c182.xhtml': [
		{
			'before': '<p style="text-align: justify" dir="rtl">&#1576;&#1575;&#1576;<span style="font-weight: bold; text-decoration: underline">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">&#1576;&#1575;&#1576;'
		},
		{
			'before': '</span></p>',
			'after': '</p>'
		}
	],
	'c162.xhtml': [
		{
			'before': 'Chapater',
			'after': 'Chapter'
		}
	], # Volume 4
	'c175.xhtml': [
		{
			'before': 'Chater',
			'after': 'Chapter'
		}
	],
	'c272.xhtml': [
		{
			'before': 'Chater',
			'after': 'Chapter'
		}
	],
	'c281.xhtml': [
		{
			'before': 'Chapaater',
			'after': 'Chapter'
		}
	],
	'c287.xhtml': [
		{
			'before': 'Chater',
			'after': 'Chapter'
		}
	],
	'c315.xhtml': [
		{
			'before': 'Chater',
			'after': 'Chapter'
		}
	],
	'c325.xhtml': [
		{
			'before': 'Chater',
			'after': 'Chapter'
		}
	], # Volume 5
	'c135.xhtml': [
		{
			'before': '<p style="font-weight: bold; text-align: justify" dir="rtl">&#1576;<span style="text-decoration: underline">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">&#1576;'
		},
		{
			'before': '</span></p>',
			'after': '</p>'
		}
	],
	'c336.xhtml': [
		{
			'before': 'Chhapter 140',
			'after': 'Chapter 140'
		}
	], # Volume 6
	'c161.xhtml': [
		{
			'before': 'Chapater 16',
			'after': 'Chapter 16'
		}
	],
	'c241.xhtml': [
		{
			'before': '<p style="text-align: justify; text-decoration: underline" dir="rtl"><span style="font-weight: bold">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">'
		},
		{
			'before': '</span></p>',
			'after': '</p>'
		}
	], # Volume 7
	'c046.xhtml': [
		{
			'before': 'Chapter&#160; 1b',
			'after': 'Chapter 1b'
		}
	],
	'c290.xhtml': [
		{
			'before': '<p style="font-weight: bold; text-align: justify" dir="rtl">',
			'after': '<p style="text-align: justify; font-weight: bold; text-decoration: underline" dir="rtl">'
		}
	]
}

def file_correction(filepath: str, content: str) -> str:
	filename = os.path.basename(filepath)
	
	if filename in CORRECTIONS:
		corrections = CORRECTIONS[filename]
		for correction in corrections:
			content = content.replace(correction['before'], correction['after'])

	return content
