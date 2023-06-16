use crate::ast::Literal;
use base64::{alphabet, engine, Engine as _};
use nom::branch::alt;
use nom::bytes::complete::{is_not, tag, tag_no_case, take_while, take_while_m_n};
use nom::character::complete::{char, digit1, one_of};
use nom::combinator::{cut, map, map_res, opt, recognize, value, verify};
use nom::error::{Error, ParseError};
use nom::multi::many0;
use nom::sequence::{delimited, pair, tuple};
use nom::IResult;
use nom::ParseTo;
use time::{Date, Month};

pub fn parse_float(inp: &str) -> IResult<&str, f64> {
    let (i, float_str) = recognize(verify(
        tuple((
            opt(one_of("+-")),
            digit1,
            opt(pair(char('.'), opt(digit1))),
            opt(tuple((one_of("eE"), opt(one_of("+-")), cut(digit1)))),
        )),
        // We need at least a fraction or an exponent for a valid float
        |(_, _, frac, exp)| frac.is_some() || exp.is_some(),
    ))(inp)?;

    match float_str.parse_to() {
        Some(f) => Ok((i, f)),
        None => Err(nom::Err::Error(Error::from_error_kind(
            i,
            nom::error::ErrorKind::Float,
        ))),
    }
}

pub fn parse_string(inp: &str) -> IResult<&str, String> {
    let part = alt((
        is_not("'"),
        // Double SQUOTE within a string escapes to a single SQUOTE
        value("'", tag("''")),
    ));

    let str_parts = delimited(char('\''), many0(part), char('\''));
    map(str_parts, |p| p.join(""))(inp)
}

// nom has its own `is_hex_digit`, but it only works on `u8`
fn is_hex_digit(c: char) -> bool {
    c.is_digit(16)
}

fn is_digit(c: char) -> bool {
    c.is_digit(10)
}

fn is_base64url_char(c: char) -> bool {
    c.is_ascii_alphanumeric() || c == '-' || c == '_' || c == '='
}

pub fn parse_guid(inp: &str) -> IResult<&str, String> {
    let (i, guid_str) = recognize(tuple((
        take_while_m_n(8, 8, is_hex_digit),
        char('-'),
        take_while_m_n(4, 4, is_hex_digit),
        char('-'),
        take_while_m_n(4, 4, is_hex_digit),
        char('-'),
        take_while_m_n(4, 4, is_hex_digit),
        char('-'),
        take_while_m_n(12, 12, is_hex_digit),
    )))(inp)?;

    Ok((i, guid_str.to_string()))
}

pub fn parse_year(inp: &str) -> IResult<&str, i32> {
    let parser = recognize(tuple((opt(char('-')), take_while_m_n(4, 4, is_digit))));

    map_res(parser, |s: &str| s.parse::<i32>())(inp)
}

pub fn parse_month(inp: &str) -> IResult<&str, Month> {
    let parser = recognize(tuple((one_of("01"), take_while_m_n(1, 1, is_digit))));

    map_res(parser, |s: &str| {
        // We can unwrap this since we parse only 2 digits anyway
        let month_num = s.parse::<u8>().unwrap();
        Month::try_from(month_num)
    })(inp)
}

pub fn parse_day(inp: &str) -> IResult<&str, u8> {
    let parser = recognize(tuple((one_of("0123"), take_while_m_n(1, 1, is_digit))));

    map_res(parser, |s: &str| s.parse::<u8>())(inp)
}

pub fn parse_date(inp: &str) -> IResult<&str, Date> {
    // OData `year`s can be negative, conflicting with ISO8601.
    // So we don't use `time::*::parse`
    let parser = tuple((parse_year, char('-'), parse_month, char('-'), parse_day));

    map_res(parser, |(y, _, m, _, d)| Date::from_calendar_date(y, m, d))(inp)
}

pub fn parse_binary(inp: &str) -> IResult<&str, Vec<u8>> {
    let binval = take_while(is_base64url_char);
    let parser = delimited(tag_no_case("binary'"), binval, char('\''));

    // TODO: map base64::DecodeError onto a nom Error for clarity
    map_res(parser, |b64| {
        // We make no assumptions about how the client handles b64 padding:
        let cfg = engine::GeneralPurposeConfig::new()
            .with_decode_padding_mode(engine::DecodePaddingMode::Indifferent);
        let engine = engine::GeneralPurpose::new(&alphabet::URL_SAFE, cfg);
        engine.decode(b64)
    })(inp)
}

pub fn parse_literal(inp: &str) -> IResult<&str, Literal> {
    let null = value(Literal::Null, tag("null"));

    let bool = alt((
        value(Literal::Boolean(true), tag_no_case("true")),
        value(Literal::Boolean(false), tag_no_case("false")),
    ));

    let int = map(nom::character::complete::i64, Literal::Integer);
    let float = alt((
        map(parse_float, Literal::Float),
        value(Literal::Float(f64::NAN), tag("NaN")),
        value(Literal::Float(f64::INFINITY), tag("INF")),
        value(Literal::Float(f64::NEG_INFINITY), tag("-INF")),
    ));

    let string = map(parse_string, Literal::String);
    let guid = map(parse_guid, Literal::GUID);
    let binary = map(parse_binary, Literal::Binary);

    let date = map(parse_date, Literal::Date);

    alt((null, bool, string, date, guid, float, int, binary))(inp)
}

#[cfg(test)]
mod tests {
    use super::*;
    use time::Month;

    fn assert_parsed_to<T>(result: IResult<&str, T>, exp: T)
    where
        T: std::fmt::Debug + std::cmp::PartialEq,
    {
        assert!(result.is_ok(), "{:?}", result);
        match result {
            Ok((rest, node)) => {
                assert!(rest.is_empty(), "Unparsed input: {rest}");
                assert_eq!(node, exp);
            }
            _ => panic!("Shouldn't occur"),
        }
    }

    #[test]
    fn parse_null() {
        assert_parsed_to(parse_literal("null"), Literal::Null);
    }

    #[test]
    fn parse_boolean() {
        assert_parsed_to(parse_literal("true"), Literal::Boolean(true));
        assert_parsed_to(parse_literal("True"), Literal::Boolean(true));
        assert_parsed_to(parse_literal("false"), Literal::Boolean(false));
        assert_parsed_to(parse_literal("False"), Literal::Boolean(false));
    }

    #[test]
    fn parse_integer() {
        assert_parsed_to(parse_literal("0"), Literal::Integer(0));
        assert_parsed_to(parse_literal("123456789"), Literal::Integer(123456789));
        assert_parsed_to(parse_literal("+123456789"), Literal::Integer(123456789));
        assert_parsed_to(parse_literal("-123456789"), Literal::Integer(-123456789));
    }

    #[test]
    fn parse_float() {
        assert_parsed_to(parse_literal("0.1"), Literal::Float(0.1));
        assert_parsed_to(parse_literal("-0.1"), Literal::Float(-0.1));
        assert_parsed_to(parse_literal("1e10"), Literal::Float(1e10));
        assert_parsed_to(parse_literal("-1e10"), Literal::Float(-1e10));
        assert_parsed_to(parse_literal("1e-10"), Literal::Float(1e-10));
        assert_parsed_to(parse_literal("1E-10"), Literal::Float(1e-10));
        assert_parsed_to(parse_literal("123.456e10"), Literal::Float(123.456e10));
        assert_parsed_to(parse_literal("INF"), Literal::Float(f64::INFINITY));
        assert_parsed_to(parse_literal("-INF"), Literal::Float(f64::NEG_INFINITY));

        // NaN never tests equal:
        match parse_literal("NaN") {
            Ok(("", Literal::Float(nan))) => assert!(nan.is_nan()),
            _ => assert!(false),
        };
    }

    #[test]
    fn parse_string() {
        assert_parsed_to(
            parse_literal("'hello world'"),
            Literal::String("hello world".to_string()),
        );
        assert_parsed_to(parse_literal("''"), Literal::String("".to_string()));
        assert_parsed_to(
            parse_literal("'g''day sir'"),
            Literal::String("g'day sir".to_string()),
        );
    }

    #[test]
    fn parse_guid() {
        let guid = "d13efbec-aa20-47f4-8756-c38852488b6e";
        assert_parsed_to(parse_literal(&guid), Literal::GUID(guid.to_string()));
        assert_parsed_to(
            parse_literal(&guid.to_ascii_uppercase()),
            Literal::GUID(guid.to_ascii_uppercase()),
        );
    }

    #[test]
    fn parse_date() {
        assert_parsed_to(
            parse_literal("2023-01-01"),
            Literal::Date(Date::from_calendar_date(2023, Month::January, 1).unwrap()),
        );
        assert_parsed_to(
            parse_literal("-0001-01-01"),
            Literal::Date(Date::from_calendar_date(-1, Month::January, 1).unwrap()),
        );
    }

    #[test]
    fn parse_binary() {
        let data = b"Definitely not a virus";

        let data_padded = engine::general_purpose::URL_SAFE.encode(data);
        assert_parsed_to(
            parse_literal(&format!("binary'{data_padded}'")),
            Literal::Binary(data.to_vec()),
        );

        let data_not_padded = engine::general_purpose::URL_SAFE_NO_PAD.encode(data);
        assert_parsed_to(
            parse_literal(&format!("binary'{data_not_padded}'")),
            Literal::Binary(data.to_vec()),
        );
    }
}
