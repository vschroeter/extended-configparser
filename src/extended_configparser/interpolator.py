from __future__ import annotations

import configparser
import os
import re


class EnvInterpolation(configparser.ExtendedInterpolation):
    """
    Interpolation which expands environment variables in values.
    Subclass of ExtendedInterpolation, thus it also supports the ${section:option} syntax.

    To interpolate environment variables in values, use the following syntax:
    value = ${ENV_VAR_NAME}
    """

    ENV_PATTERN = re.compile(r"\$\[([^\}]+)\]")
    _KEYCRE = re.compile(r"\$\{([^}]+)\}")

    def __init__(self, allow_uninterpolated_values: bool = False) -> None:
        self.allow_uninterpolated_values = allow_uninterpolated_values

    def _interpolate_some(self, parser, option, accum, rest, section, map, depth) -> None:  # type: ignore
        rawval = parser.get(section, option, raw=True, fallback=rest)

        if depth > configparser.MAX_INTERPOLATION_DEPTH:
            raise configparser.InterpolationDepthError(option, section, rawval)
        while rest:
            rest = os.path.expandvars(rest)
            p = rest.find("$")
            if p < 0:
                accum.append(rest)
                return
            if p > 0:
                accum.append(rest[:p])
                rest = rest[p:]
            # p is no longer used
            c = rest[1:2]

            # If it's an escaped $
            if c == "$":
                accum.append("$")
                rest = rest[2:]
            elif c == "{":
                m = self._KEYCRE.match(rest)
                if m is None:
                    raise configparser.InterpolationSyntaxError(
                        option,
                        section,
                        "bad interpolation variable reference %r" % rest,
                    )
                path = m.group(1).split(":")
                rest = rest[m.end() :]
                sect = section
                opt = option
                try:
                    if len(path) == 1:
                        # Substitute env vars
                        if path[0] in os.environ:
                            v = os.environ[path[0]]
                        else:
                            opt = parser.optionxform(path[0])
                            v = map[opt]
                    elif len(path) == 2:
                        sect = path[0]
                        opt = parser.optionxform(path[1])
                        if self.allow_uninterpolated_values:
                            if not parser.has_option(sect, opt):
                                accum.append("$" + c + ":".join(path))
                                continue
                        v = parser.get(sect, opt, raw=True)
                    else:
                        raise configparser.InterpolationSyntaxError(
                            option, section, "More than one ':' found: %r" % (rest,)
                        )
                except (
                    KeyError,
                    configparser.NoSectionError,
                    configparser.NoOptionError,
                ):
                    raise configparser.InterpolationMissingOptionError(
                        option, section, rawval, ":".join(path)
                    ) from None
                if "$" in v:
                    self._interpolate_some(
                        parser,
                        opt,
                        accum,
                        v,
                        sect,
                        dict(parser.items(sect, raw=True)),
                        depth + 1,
                    )
                else:
                    accum.append(v)
            else:

                if self.allow_uninterpolated_values:
                    accum.append("$" + c)
                    rest = rest[2:]
                else:
                    raise configparser.InterpolationSyntaxError(
                        option,
                        section,
                        "'$' must be followed by '$' or '{', " "found: %r" % (rest,),
                    )
