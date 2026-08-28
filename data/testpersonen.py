"""Vordefinierte Testpersonen aus dem internen Test-Datensatz
(TEST_DATA_INT3, Reiter "Extra-Daten"). Alle Namen und Adressen sind
fiktiv (wiederverwendete Test-Identitaeten auf bekannte oeffentliche
Adressen, z.B. Marienplatz/Alexanderplatz) und dienen ausschliesslich
als vorausfuellbare Auswahl fuer die Falldaten-Eingabemaske."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Testperson:
    mgl_nr: str
    vorname: str
    nachname: str
    geburtsdatum: date
    strasse: str
    plz: str
    ort: str

    @property
    def plz_ort(self) -> str:
        if self.plz and self.ort:
            return f"{self.plz} {self.ort}"
        return self.ort or self.plz

    @property
    def anzeige(self) -> str:
        return (
            f"{self.vorname} {self.nachname} — {self.mgl_nr} "
            f"({self.geburtsdatum.strftime('%d.%m.%Y')})"
        )


TESTPERSONEN: list[Testperson] = [
    Testperson('010861357', 'Test', 'OmnIA', date(1974, 5, 16), 'Marienplatz 1', '80331', 'München'),
    Testperson('010861390', 'Lukas', 'OmnIA', date(1973, 2, 10), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010861365', 'Anna', 'OmnIA', date(1970, 11, 21), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010861403', 'Tim', 'OmnIA', date(1971, 1, 6), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010861373', 'Maria', 'OmnIA', date(1999, 12, 9), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010861411', 'Maria', 'OmnIA', date(1985, 1, 8), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010861446', 'Lukas', 'OmnIA', date(1965, 9, 20), 'Marienplatz 1', '80331', 'München'),
    Testperson('010861420', 'Leon', 'OmnIA', date(1982, 12, 13), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010861454', 'Maria', 'OmnIA', date(2002, 6, 9), 'Marienplatz 1', '80331', 'München'),
    Testperson('010861438', 'Paul', 'OmnIA', date(2005, 3, 11), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010861462', 'Lukas', 'OmnIA', date(1993, 6, 4), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010861470', 'Tim', 'OmnIA', date(1978, 4, 7), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010861497', 'Paul', 'OmnIA', date(1990, 9, 19), 'Marienplatz 1', '80331', 'München'),
    Testperson('010861489', 'Leon', 'OmnIA', date(1963, 6, 12), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010861500', 'Postman', 'OmnIA', date(1979, 12, 29), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010861292', 'Anna', 'OmnIA', date(1976, 5, 20), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010861268', 'Postman', 'OmnIA', date(1986, 9, 25), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010861250', 'Anna', 'OmnIA', date(1992, 10, 17), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010861276', 'Leon', 'OmnIA', date(1973, 5, 9), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010861306', 'Laura', 'OmnIA', date(1967, 8, 30), 'Marienplatz 1', '80331', 'München'),
    Testperson('010861284', 'Test', 'OmnIA', date(1974, 6, 19), 'Marienplatz 1', '80331', 'München'),
    Testperson('010861322', 'Tim', 'OmnIA', date(2000, 10, 5), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010861349', 'Leon', 'OmnIA', date(1972, 11, 25), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010861330', 'Anna', 'OmnIA', date(1971, 2, 28), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010861314', 'Max', 'OmnIA', date(1980, 2, 27), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862191', 'Emma', 'OmnIA', date(1973, 2, 19), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862213', 'Leon', 'OmnIA', date(1982, 1, 19), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862248', 'Max', 'OmnIA', date(1971, 8, 11), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862205', 'Laura', 'OmnIA', date(1966, 1, 10), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862230', 'Tim', 'OmnIA', date(1982, 8, 7), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862264', 'Leon', 'OmnIA', date(1965, 10, 6), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862256', 'Max', 'OmnIA', date(1974, 10, 10), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862280', 'Anna', 'OmnIA', date(1995, 9, 18), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862272', 'Postman', 'OmnIA', date(1960, 4, 18), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862302', 'Test', 'OmnIA', date(1969, 9, 28), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862310', 'Postman', 'OmnIA', date(1971, 11, 8), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862329', 'Test', 'OmnIA', date(1983, 6, 22), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862353', 'Anna', 'OmnIA', date(1962, 9, 24), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862345', 'Anna', 'OmnIA', date(1983, 8, 19), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862337', 'Emma', 'OmnIA', date(1990, 1, 6), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862361', 'Max', 'OmnIA', date(2001, 4, 7), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862370', 'Paul', 'OmnIA', date(1989, 11, 13), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862388', 'Laura', 'OmnIA', date(2002, 8, 3), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862396', 'Chris', 'Barker', date(1950, 10, 16), 'Hansastraße 19', '', ''),
    Testperson('010862400', 'Paul', 'OmnIA', date(1994, 11, 13), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862418', 'Lukas', 'OmnIA', date(1977, 8, 19), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862426', 'Anna', 'OmnIA', date(2004, 6, 17), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862450', 'Test', 'OmnIA', date(1978, 10, 17), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862442', 'Anna', 'OmnIA', date(1975, 5, 31), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862434', 'Laura', 'OmnIA', date(1990, 3, 10), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862469', 'Lukas', 'OmnIA', date(1988, 6, 24), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862477', 'Sophie', 'OmnIA', date(1963, 9, 24), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862485', 'Leon', 'OmnIA', date(1967, 7, 28), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862493', 'Lukas', 'OmnIA', date(1963, 7, 3), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862507', 'Sophie', 'OmnIA', date(1978, 2, 11), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862515', 'Postman', 'OmnIA', date(1983, 7, 31), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862523', 'Test', 'OmnIA', date(1999, 4, 1), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862531', 'Tim', 'OmnIA', date(1997, 11, 10), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862540', 'Tim', 'OmnIA', date(1983, 11, 10), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862558', 'Tim', 'OmnIA', date(1986, 5, 4), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862574', 'Paul', 'OmnIA', date(2005, 6, 28), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862566', 'Tim', 'OmnIA', date(1975, 3, 30), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862590', 'Paul', 'OmnIA', date(2002, 1, 5), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862582', 'Laura', 'OmnIA', date(1985, 6, 29), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862604', 'Max', 'OmnIA', date(1968, 4, 22), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862612', 'Maria', 'OmnIA', date(1980, 10, 24), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862620', 'Max', 'OmnIA', date(1964, 6, 23), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862639', 'Laura', 'OmnIA', date(1966, 2, 13), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862655', 'Leon', 'OmnIA', date(1963, 10, 5), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862647', 'Tim', 'OmnIA', date(1976, 3, 20), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862663', 'Sophie', 'OmnIA', date(1986, 6, 26), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862671', 'Postman', 'OmnIA', date(1977, 4, 14), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862680', 'Postman', 'OmnIA', date(1979, 3, 9), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862701', 'Max', 'OmnIA', date(1960, 2, 4), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862698', 'Sophie', 'OmnIA', date(1993, 6, 18), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862710', 'Sophie', 'OmnIA', date(1995, 5, 2), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862728', 'Test', 'OmnIA', date(1984, 10, 12), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862736', 'Postman', 'OmnIA', date(1981, 9, 15), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862744', 'Leon', 'OmnIA', date(1967, 8, 5), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862752', 'Tim', 'OmnIA', date(1968, 7, 28), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862760', 'Sophie', 'OmnIA', date(1970, 9, 13), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862779', 'Tim', 'OmnIA', date(1967, 4, 23), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862787', 'Postman', 'OmnIA', date(1968, 2, 28), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862795', 'Lukas', 'OmnIA', date(2003, 8, 23), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862809', 'Emma', 'OmnIA', date(2005, 6, 1), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862817', 'Emma', 'OmnIA', date(1964, 9, 17), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862825', 'Max', 'OmnIA', date(1982, 5, 15), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862833', 'Emma', 'OmnIA', date(1999, 1, 12), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862850', 'Tim', 'OmnIA', date(1975, 8, 27), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862841', 'Test', 'OmnIA', date(1995, 12, 17), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862868', 'Laura', 'OmnIA', date(1962, 3, 16), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862876', 'Laura', 'OmnIA', date(1975, 12, 6), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862884', 'Postman', 'OmnIA', date(1998, 11, 7), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862892', 'Postman', 'OmnIA', date(1994, 12, 10), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862906', 'Leon', 'OmnIA', date(1993, 8, 6), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862914', 'Paul', 'OmnIA', date(1997, 5, 8), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862922', 'Maria', 'OmnIA', date(1965, 3, 28), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862930', 'Paul', 'OmnIA', date(1963, 1, 30), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010862949', 'Emma', 'OmnIA', date(1983, 5, 12), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010862957', 'Sophie', 'OmnIA', date(1997, 4, 27), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010862965', 'Max', 'OmnIA', date(2003, 12, 25), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862973', 'Anna', 'OmnIA', date(1983, 4, 19), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010862981', 'Sophie', 'OmnIA', date(1998, 11, 1), 'Marienplatz 1', '80331', 'München'),
    Testperson('010862990', 'Anna', 'OmnIA', date(1987, 7, 21), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010863007', 'Anna', 'OmnIA', date(1977, 11, 22), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010863015', 'Laura', 'OmnIA', date(1968, 1, 15), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010863023', 'Anna', 'OmnIA', date(2005, 10, 27), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010863031', 'Maria', 'OmnIA', date(1993, 4, 19), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010863040', 'Laura', 'OmnIA', date(2005, 1, 22), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010863058', 'Max', 'OmnIA', date(1979, 7, 20), 'Marienplatz 1', '80331', 'München'),
    Testperson('010863066', 'Test', 'OmnIA', date(1977, 3, 8), 'Domkloster 4', '50667', 'Köln'),
    Testperson('010863074', 'Lukas', 'OmnIA', date(1980, 5, 11), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010863082', 'Laura', 'OmnIA', date(1991, 5, 19), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010863090', 'Tim', 'OmnIA', date(1991, 1, 10), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010863104', 'Laura', 'OmnIA', date(1961, 5, 19), 'Schiffbeker Weg 199', '22119', 'Hamburg'),
    Testperson('010858674', 'Maria', 'OmnIA', date(2002, 10, 24), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010859328', 'Lukas', 'OmnIA', date(1976, 5, 11), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010859310', 'Max', 'OmnIA', date(1999, 11, 22), 'Alexanderplatz 1', '10178', 'Berlin'),
    Testperson('010859344', 'Laura', 'OmnIA', date(1973, 11, 3), 'Zeil 106', '60313', 'Frankfurt am Main'),
    Testperson('010859379', 'Laura', 'OmnIA', date(1971, 6, 5), 'Zeil 106', '60313', 'Frankfurt am Main'),
]
