<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
                xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                exclude-result-prefixes="m w">

    <xsl:output method="text" indent="no"/>

    <xsl:template match="/">
        <xsl:apply_templates select="*"/>
    </xsl:template>

    <xsl:template match="*[local-name()='oMath'] | *[local-name()='oMathPara']">
        <xsl:apply_templates/>
    </xsl:template>

    <!-- Fraction: \frac{num}{den} -->
    <xsl:template match="*[local-name()='f']">
        <xsl:text>\frac{</xsl:text>
        <xsl:apply_templates select="*[local-name()='num']"/>
        <xsl:text>}{</xsl:text>
        <xsl:apply_templates select="*[local-name()='den']"/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- Superscript: base^{sup} -->
    <xsl:template match="*[local-name()='sup']">
        <xsl:apply_templates select="*[local-name()='e']"/>
        <xsl:text>^{</xsl:text>
        <xsl:apply_templates select="*[local-name()='sup']"/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- Subscript: base_{sub} -->
    <xsl:template match="*[local-name()='sub']">
        <xsl:apply_templates select="*[local-name()='e']"/>
        <xsl:text>_{</xsl:text>
        <xsl:apply_templates select="*[local-name()='sub']"/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- Sub-Superscript: base_{sub}^{sup} -->
    <xsl:template match="*[local-name()='sSubSup']">
        <xsl:apply_templates select="*[local-name()='e']"/>
        <xsl:text>_{</xsl:text>
        <xsl:apply_templates select="*[local-name()='sub']"/>
        <xsl:text>}^{</xsl:text>
        <xsl:apply_templates select="*[local-name()='sup']"/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- Delimiter: \left( ... \right] etc -->
    <xsl:template match="*[local-name()='d']">
        <xsl:variable name="dPr" select="*[local-name()='dPr']"/>
        <xsl:variable name="open" select="$dPr/*[local-name()='begChr']/@*[local-name()='val']"/>
        <xsl:variable name="close" select="$dPr/*[local-name()='endChr']/@*[local-name()='val']"/>
        
        <xsl:choose>
            <xsl:when test="$open='(' or not($open)">\left(</xsl:when>
            <xsl:when test="$open='['">\left[</xsl:when>
            <xsl:when test="$open='{'">\left\{</xsl:when>
            <xsl:when test="$open='|'">\left|</xsl:when>
            <xsl:otherwise>\left.</xsl:otherwise>
        </xsl:choose>
        <xsl:apply_templates select="*[local-name()='e']"/>
        <xsl:choose>
            <xsl:when test="$close=')' or not($close)">\right)</xsl:when>
            <xsl:when test="$close=']'">\right]</xsl:when>
            <xsl:when test="$close='}'">\right\}</xsl:when>
            <xsl:when test="$close='|'">\right|</xsl:when>
            <xsl:otherwise>\right.</xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Matrix: \begin{matrix} ... \end{matrix} -->
    <xsl:template match="*[local-name()='m']">
        <xsl:text>\begin{matrix}</xsl:text>
        <xsl:for-each select="*[local-name()='mr']">
            <xsl:for-each select="*[local-name()='e']">
                <xsl:apply_templates/>
                <xsl:if test="position() != last()">
                    <xsl:text> &amp; </xsl:text>
                </xsl:if>
            </xsl:for-each>
            <xsl:if test="position() != last()">
                <xsl:text> \\ </xsl:text>
            </xsl:if>
        </xsl:for-each>
        <xsl:text>\end{matrix}</xsl:text>
    </xsl:template>

    <!-- Accents: \vec{}, \bar{}, \hat{} -->
    <xsl:template match="*[local-name()='acc']">
        <xsl:variable name="accPr" select="*[local-name()='accPr']"/>
        <xsl:variable name="chr" select="$accPr/*[local-name()='chr']/@*[local-name()='val']"/>
        
        <xsl:choose>
            <xsl:when test="$chr='⃗' or $chr='→' or $chr='?' or contains('?→⃗', $chr)">\vec{</xsl:when>
            <xsl:when test="$chr='¯' or $chr='-'">\bar{</xsl:when>
            <xsl:when test="$chr='^'">\hat{</xsl:when>
            <xsl:otherwise>\tilde{</xsl:otherwise>
        </xsl:choose>
        <xsl:apply_templates select="*[local-name()='e']"/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- Radicals: \sqrt{} or \sqrt[n]{} -->
    <xsl:template match="*[local-name()='rad']">
        <xsl:variable name="radPr" select="*[local-name()='radPr']"/>
        <xsl:variable name="degHide" select="$radPr/*[local-name()='degHide']/@*[local-name()='val']"/>
        <xsl:variable name="deg" select="*[local-name()='deg']"/>
        
        <xsl:choose>
            <xsl:when test="$degHide='1' or not($deg) or normalize-space(string($deg))=''">
                <xsl:text>\sqrt{</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>\sqrt[</xsl:text>
                <xsl:apply_templates select="$deg"/>
                <xsl:text>]{</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply_templates select="*[local-name()='e']"/>
        <xsl:text>}</xsl:text>
    </xsl:template>

    <!-- Numbering/Grouping (rare) -->
    <xsl:template match="*[local-name()='groupChr']">
        <xsl:apply_templates select="*[local-name()='e']"/>
    </xsl:template>

    <!-- Normal Runs and Text Nodes -->
    <xsl:template match="*[local-name()='r']">
        <xsl:apply_templates select="*[local-name()='t']"/>
    </xsl:template>

    <xsl:template match="*[local-name()='t']">
        <xsl:value-of select="."/>
    </xsl:template>

    <xsl:template match="*[local-name()='ctrlPr'] | *[local-name()='dPr'] | *[local-name()='mPr'] | *[local-name()='fPr']"/>

    <!-- Catch-all with recursion -->
    <xsl:template match="*">
        <xsl:apply_templates/>
    </xsl:template>

</xsl:stylesheet>
